import strawberry
from app.graphql.AuthExtension import AuthExtension
from app.graphql.User.UserResolver import UserQuery, UserMutation
from app.graphql.Authentication.AuthResolver import AuthQuery, AuthMutation
from app.graphql.Country.CountryResolver import CountryQuery
from app.graphql.SocialMedia.SocialMediaResolver import SocialMediaQuery
from app.graphql.UserSocialNetwork.UserSocialNetowrkResolver import UserSocialNetworkQuery, UserSocialNetworkMutation
from app.graphql.Category.CategoryResolver import  CategoryQuery
from app.graphql.Publishing.PublishingResolver import PublishingQuery
from app.graphql.Software.SoftwareResolver import SoftwareQuery
from app.graphql.Artwork.ArtworkResolver import ArtworkMutation, ArtworkQuery, ArtworkSubscription
from app.graphql.Topic.TopicResolver import TopicQuery
from app.graphql.UserSkills.UserSkillsResolver import UserSkillsQuery, UserSkillsMutation
from app.graphql.ArtworkStatistics.ArtworkStatisticsResolver import ArtworkStatisticsMutation, ArtworkStatisticsQuery
from app.graphql.ArtworkViews.ArtworkViewsResolver import ArtworkViewsMutation
from app.graphql.Follow.FollowResolver import FollowMutation, FollowQuery
from app.graphql.Chat.ChatResolver import ChatQuery, ChatMutation, ChatSubscription
from app.graphql.Block.BlockResolver import BlockMutation

@strawberry.type
class Query(AuthQuery, UserQuery, CountryQuery, UserSkillsQuery, SocialMediaQuery, UserSocialNetworkQuery, CategoryQuery, PublishingQuery, SoftwareQuery, TopicQuery, ArtworkQuery, ArtworkStatisticsQuery, FollowQuery, ChatQuery):
    pass

@strawberry.type
class Mutation(AuthMutation, UserMutation, UserSkillsMutation, UserSocialNetworkMutation, ArtworkMutation, ArtworkStatisticsMutation, ArtworkViewsMutation, FollowMutation, ChatMutation, BlockMutation):
    pass

@strawberry.type
class Subscription(ArtworkSubscription, ChatSubscription):
    pass

GraphSchema = strawberry.Schema(query=Query, mutation=Mutation, subscription=Subscription, extensions=[AuthExtension()])
