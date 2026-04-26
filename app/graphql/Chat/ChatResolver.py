import asyncio
import strawberry
from app.config.logger import logger
from app.utils.helpers import Helpers
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from strawberry.exceptions import GraphQLError
from app.graphql.Chat.ChatInputs import SetChatInput, DeleteChatInput
from app.graphql.Standard.StandardInputs import PaginationInput
from app.graphql.Chat.ChatPayloads import SingleChatPayload, SetChatPayload, ChatMessagePayload, ChatsPayload, ArtistPayload, LastMessagePayload
from app.services.Chat.ChatService import ChatService
from app.services.User.UserService import UserService
from app.services.Chat.MessageService import MessageService
from app.services.Follow.FollowService import FollowService
from app.services.Block.BlockService import BlockService
from typing import AsyncGenerator
from app.services.PubSub.RedisPubSub import PubSubManager

@strawberry.type
class ChatQuery:
    @strawberry.field
    async def getChats(self, info, pagination: PaginationInput) -> list[ChatsPayload]:
        db = info.context["mongo_db"]
        pg = info.context["db"]
        current_user = info.context["current_user"]

        chat_service = ChatService(db)
        user_service = UserService(pg)
        follow_service = FollowService(pg)
        block_service = BlockService(pg)

        try:
            getChats = await chat_service.getChats(userId=current_user.userId, limit=pagination.limit, offset=pagination.offset)
            if not getChats.get("ok", False):
                raise GraphQLError(message=getChats['error'], extensions={"code": "NOT_FOUND"})

            chats = getChats.get("data")

            async def fetch_chat_details(chat):
                artistData, relationship, isBlockedUser, userHasBlockedMe = await asyncio.gather(
                    user_service.getUserGeneralData(userId=chat['artistId']),
                    follow_service.verifyRelationship(followerId=current_user.userId, followedId=chat['artistId']),
                    block_service.verifyBlock(blockerId=current_user.userId, blockedId=chat['artistId']),
                    block_service.verifyBlock(blockerId=chat['artistId'], blockedId=current_user.userId)
                )
                return chat, artistData, relationship, isBlockedUser, userHasBlockedMe
            
            detailedResults = await asyncio.gather(*(fetch_chat_details(chat) for chat in chats))
            
            response = []
            for chat, getArtist, getRelationship, checkIsBlocked, checkImBlocked in detailedResults:
                if not getArtist["ok"]:
                    # raise GraphQLError(message=get_artist['error'], extensions={"code": "NOT_FOUND"})
                    continue
                    
                relationship = getRelationship['data'] if getRelationship['ok'] else None
                isBlockedState = checkIsBlocked['data'] if checkIsBlocked['ok'] else None
                imBlockedState = checkImBlocked['data'] if checkImBlocked['ok'] else None

                artist = getArtist["data"]
                lastMessage = chat['last_message']
                isFollowing = False if relationship is None else relationship['exists']
                isBlocked = False if isBlockedState is None else isBlockedState['exists']
                hasBlockedMe = False if imBlockedState is None else imBlockedState['exists']

                artist_payload = ArtistPayload(
                    artistId=artist['user_id'], 
                    username=artist['username'], 
                    avatar=artist['avatar']
                )
                
                lastMessage_payload = LastMessagePayload(
                    userId=lastMessage['user_id'], 
                    message=lastMessage['message'], 
                    date=lastMessage['date'], 
                    time=lastMessage['time']
                )

                response.append(ChatsPayload(
                    chatId=str(chat['chatId']), 
                    artist=artist_payload, 
                    lastMessage=lastMessage_payload,
                    isFollowing=isFollowing,
                    isBlocked=isBlocked,
                    hasBlockedMe=hasBlockedMe
                ))

            return response

        except GraphQLError as e:
            logger.error(e.message)
            raise e

        except Exception as e:
            error_mapping = {
                IntegrityError: ("BAD_USER_INPUT", "E-mail already in used"),
                SQLAlchemyError: ("INTERNAL_SERVER_ERROR", "Error interno del servidor"),
                ValueError: ("BAD_USER_INPUT", "Datos inválidos"),
                PermissionError: ("FORBIDDEN", "Permiso denegado"),
                FileNotFoundError: ("NOT_FOUND", "Archivo no encontrado"),
                ConnectionError: ("TOO_MANY_REQUESTS", "Demasiadas solicitudes"),
            }

            extension_code, error_message = error_mapping.get(type(e), ("INTERNAL_SERVER_ERROR", "Error desconocido"))
            logger.error(error_message)
            raise GraphQLError(message=error_message, extensions={"code": extension_code})

    @strawberry.field
    async def getChatArtist(self, info, chatId: str, pagination: PaginationInput) -> SingleChatPayload:
        db = info.context["mongo_db"]

        chat_service = ChatService(db)

        try:
            get_chat = await chat_service.getChat(chatId=chatId, limit=pagination.limit, offset=pagination.offset)
            if not get_chat.get("ok", False):
                raise GraphQLError(message=get_chat['error'], extensions={"code": "NOT_FOUND"})

            chat = get_chat.get("data")

            return SingleChatPayload(messages=chat['messages'], hasMore=chat['hasMore'])

        except GraphQLError as e:
            logger.error(e.message)
            raise e

        except Exception as e:
            error_mapping = {
                IntegrityError: ("BAD_USER_INPUT", "E-mail already in used"),
                SQLAlchemyError: ("INTERNAL_SERVER_ERROR", "Error interno del servidor"),
                ValueError: ("BAD_USER_INPUT", "Datos inválidos"),
                PermissionError: ("FORBIDDEN", "Permiso denegado"),
                FileNotFoundError: ("NOT_FOUND", "Archivo no encontrado"),
                ConnectionError: ("TOO_MANY_REQUESTS", "Demasiadas solicitudes"),
            }

            extension_code, error_message = error_mapping.get(type(e), ("INTERNAL_SERVER_ERROR", "Error desconocido"))
            logger.error(error_message)
            raise GraphQLError(message=error_message, extensions={"code": extension_code})
        
@strawberry.type
class ChatMutation:
    @strawberry.mutation
    async def setChatMessage(self, info, chat: SetChatInput) -> SetChatPayload:
        db = info.context["mongo_db"]
        request = info.context["request"]
        current_user = info.context["current_user"]

        chat_service = ChatService(db)
        message_service = MessageService(db)
        
        ip = await Helpers.getIp(request)
        terminal = await Helpers.getRequestAgents(request)

        try:
            chatId = chat.chatId

            if chatId is None:
                set_chat = await chat_service.setChat(userA=current_user.userId, userB=chat.artistId, ip=ip, terminal=terminal)
                if not set_chat.get("ok", False):
                    raise GraphQLError(message=set_chat['error'], extensions={"code": "NOT_FOUND"})
                
                chatId = set_chat.get("data")

            message = chat.message

            set_message = await message_service.setMessage(
                chatId=chatId, 
                userId=message.userId, 
                typeMessage=message.typeMessage, 
                message=message.message, 
                createdAt=message.createdAt,
                ip=ip,
                terminal=terminal
            )
            if not set_message.get("ok", False):
                raise GraphQLError(message=set_message['error'], extensions={"code": "NOT_FOUND"})
            
            messageId = set_message.get("data")

            add_message = await chat_service.addMessage(chatId=chatId, messageId=messageId, message=message)
            if not add_message.get("ok", False):
                raise GraphQLError(message=add_message['error'], extensions={"code": "NOT_FOUND"})
            
            new_message_data = await message_service.getMessageById(messageId=messageId)
            if not new_message_data.get("ok", False):
                raise GraphQLError(message=new_message_data['error'], extensions={"code": "NOT_FOUND"})
            
            message_redis = new_message_data.get("data")
            message_redis['date'] = message.date

            pubsub_manager = PubSubManager() 
            await pubsub_manager.publish(f"chat_{chatId}", message_redis)

            return SetChatPayload(chatId=chatId)

        except GraphQLError as e:
            logger.error(e.message)
            raise e

        except Exception as e:
            error_mapping = {
                IntegrityError: ("BAD_USER_INPUT", "E-mail already in used"),
                SQLAlchemyError: ("INTERNAL_SERVER_ERROR", "Error interno del servidor"),
                ValueError: ("BAD_USER_INPUT", "Datos inválidos"),
                PermissionError: ("FORBIDDEN", "Permiso denegado"),
                FileNotFoundError: ("NOT_FOUND", "Archivo no encontrado"),
                ConnectionError: ("TOO_MANY_REQUESTS", "Demasiadas solicitudes"),
            }

            extension_code, error_message = error_mapping.get(type(e), ("INTERNAL_SERVER_ERROR", "Error desconocido"))
            logger.error(error_message)
            raise GraphQLError(message=error_message, extensions={"code": extension_code})
        
    @strawberry.mutation
    async def deleteChat(self, info, input: DeleteChatInput) -> str:
        db = info.context["mongo_db"]

        chat_service = ChatService(db)
        message_service = MessageService(db)

        try:
            delete_chat_messages = await message_service.deleteMessagesByChatId(chatId=input.chatId)
            if not delete_chat_messages.get("ok", False):
                raise GraphQLError(message=delete_chat_messages['error'], extensions={"code": "NOT_FOUND"})
            
            delete_chat = await chat_service.deleteChat(chatId=input.chatId)
            if not delete_chat.get("ok", False):
                raise GraphQLError(message=delete_chat['error'], extensions={"code": "NOT_FOUND"})
            

            return delete_chat.get('message')

        except GraphQLError as e:
            logger.error(e.message)
            raise e

        except Exception as e:
            error_mapping = {
                IntegrityError: ("BAD_USER_INPUT", "E-mail already in used"),
                SQLAlchemyError: ("INTERNAL_SERVER_ERROR", "Error interno del servidor"),
                ValueError: ("BAD_USER_INPUT", "Datos inválidos"),
                PermissionError: ("FORBIDDEN", "Permiso denegado"),
                FileNotFoundError: ("NOT_FOUND", "Archivo no encontrado"),
                ConnectionError: ("TOO_MANY_REQUESTS", "Demasiadas solicitudes"),
            }

            extension_code, error_message = error_mapping.get(type(e), ("INTERNAL_SERVER_ERROR", "Error desconocido"))
            logger.error(error_message)
            raise GraphQLError(message=error_message, extensions={"code": extension_code})
        
@strawberry.type
class ChatSubscription:
    @strawberry.subscription
    async def messageSent(self, info, chatId: str) -> AsyncGenerator[ChatMessagePayload, None]:
        pubsub_manager = PubSubManager()
        channel_name = f"chat_{chatId}"
        
        async for message_data in pubsub_manager.subscribe(channel_name):
            yield ChatMessagePayload(
                chatId=message_data['chat_id'],
                messageId=message_data['_id'],
                userId=message_data['user_id'],
                typeMessage=message_data['type_message'],
                message=message_data['message'],
                createdAt=message_data['created_at'],
                date=message_data['date']
            )