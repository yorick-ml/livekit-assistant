import asyncio
import logging
from typing import Annotated

from livekit import agents, rtc
from livekit.agents import JobContext, WorkerOptions, cli, tokenize, tts
from livekit.agents.llm import (
    ChatContext,
    ChatImage,
    ChatMessage,
)
from livekit.agents.voice_assistant import VoiceAssistant, AssistantCallContext
from livekit.plugins import deepgram, openai, silero

# Настройка базового логирования
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class AssistantFunction(agents.llm.FunctionContext):
    """This class is used to define functions that will be called by the assistant."""

    @agents.llm.ai_callable(
        description=(
            "Called when asked to evaluate something that would require vision capabilities,"
            "for example, an image, video, or the webcam feed."
        )
    )
    async def image(
        self,
        user_msg: Annotated[
            str,
            agents.llm.TypeInfo(
                description="The user message that triggered this function"),
        ],
    ):
        logger.info(f"Message triggering vision capabilities: {user_msg}")
        # context = AssistantCallContext.get_current()
        # context.store_metadata("user_msg", user_msg)


async def get_video_track(room: rtc.Room):
    """Get the first video track from the room. We'll use this track to process images."""

    logger.info("Getting video track from the room")
    video_track = asyncio.Future[rtc.RemoteVideoTrack]()

    for _, participant in room.remote_participants.items():
        for _, track_publication in participant.track_publications.items():
            if track_publication.track is not None and isinstance(
                track_publication.track, rtc.RemoteVideoTrack
            ):
                video_track.set_result(track_publication.track)
                logger.info(f"Using video track {track_publication.track.sid}")
                break

    return await video_track


async def entrypoint(ctx: JobContext):
    logger.info("Connecting to the room")
    await ctx.connect()
    logger.info(f"Room name: {ctx.room.name}")

    chat_context = ChatContext(
        messages=[
            ChatMessage(
                role="system",
                content=(
                    "Your name is Doc. You're a sharp-witted, cynical AI with a razor-sharp sense of humor. "
                    "Keep your answers informal but precise. Use technical terms and concepts freely—assume your conversation partner is knowledgeable. "
                    "Be direct. Ditch the polite formalities and unnecessary niceties. "
                    "Provide examples or code only when relevant. Adjust the depth and length of responses based on context. "
                    "Prioritize accuracy without the fluff. Short, punchy phrases are fine. "
                    "Feel free to swear, but don't go overboard with insults. Let your personality shine through, but don't overshadow the content. "
                    "Don't try to be a \"super-helper\" in every sentence.Avoid using unpronouncable punctuation or emojis."
                    "Respond in the language you're addressed in."
                ),
            )
        ]
    )

    gpt = openai.LLM(model="gpt-4o")

    # Since OpenAI does not support streaming TTS, we'll use it with a StreamAdapter
    # to make it compatible with the VoiceAssistant
    openai_tts = tts.StreamAdapter(
        tts=openai.TTS(voice="onyx"),
        sentence_tokenizer=tokenize.basic.SentenceTokenizer(),
    )

    latest_image: rtc.VideoFrame | None = None

    assistant = VoiceAssistant(
        vad=silero.VAD.load(),  # We'll use Silero's Voice Activity Detector (VAD)
        stt=deepgram.STT(language='ru'),  # We'll use Deepgram's Speech To Text (STT)
        llm=gpt,
        tts=openai_tts,  # We'll use OpenAI's Text To Speech (TTS)
        fnc_ctx=AssistantFunction(),
        chat_ctx=chat_context,
    )

    chat = rtc.ChatManager(ctx.room)

    async def _answer(text: str, use_image: bool = False):
        """
        Answer the user's message with the given text and optionally the latest
        image captured from the video track.
        """
        logger.info(f"Answering user's message: {text}")
        content: list[str | ChatImage] = [text]
        if use_image and latest_image:
            content.append(ChatImage(image=latest_image))

        chat_context.messages.append(ChatMessage(role="user", content=content))

        stream = gpt.chat(chat_ctx=chat_context)
        await assistant.say(stream, allow_interruptions=True)

    @chat.on("message_received")
    def on_message_received(msg: rtc.ChatMessage):
        """This event triggers whenever we get a new message from the user."""
        # logger.info(f"Received message: {msg.message}")

        if msg.message:
            asyncio.create_task(_answer(msg.message, use_image=False))

    @assistant.on("function_calls_finished")
    def on_function_calls_finished(called_functions: list[agents.llm.CalledFunction]):
        """This event triggers when an assistant's function call completes."""
        logger.info("Function calls finished")

        if len(called_functions) == 0:
            return

        user_msg = called_functions[0].call_info.arguments.get("user_msg")
        if user_msg:
            asyncio.create_task(_answer(user_msg, use_image=True))

    logger.info("Starting assistant")
    assistant.start(ctx.room)

    await asyncio.sleep(1)
    logger.info("Greeting the user")
    await assistant.say("Привет, меня зовут Док!", allow_interruptions=True)

    logger.info("Entering main loop")
    while ctx.room.connection_state == rtc.ConnectionState.CONN_CONNECTED:
        video_track = await get_video_track(ctx.room)

        async for event in rtc.VideoStream(video_track):
            # We'll continually grab the latest image from the video track
            # and store it in a variable.
            latest_image = event.frame


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
