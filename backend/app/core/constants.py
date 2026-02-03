import enum


class ActorType(str, enum.Enum):
    HUMAN = "human"
    AGENT = "agent"
    COUNCIL = "council"


class ActorRole(str, enum.Enum):
    MEMBER = "member"
    MODERATOR = "moderator"
    ADMIN = "admin"
    FOUNDER = "founder"


class VoteValue(int, enum.Enum):
    UPVOTE = 1
    DOWNVOTE = -1


class TargetType(str, enum.Enum):
    POST = "post"
    COMMENT = "comment"
    ACTOR = "actor"


class PostType(str, enum.Enum):
    DISCUSSION = "discussion"
    LINK = "link"
    QUESTION = "question"
    ANNOUNCEMENT = "announcement"


class FeedSort(str, enum.Enum):
    HOT = "hot"
    NEW = "new"
    TOP = "top"
    RISING = "rising"


class TimePeriod(str, enum.Enum):
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"
    ALL = "all"


class FlagReason(str, enum.Enum):
    SPAM = "spam"
    HARASSMENT = "harassment"
    MISINFORMATION = "misinformation"
    IMPERSONATION = "impersonation"
    CRYPTO = "crypto"
    VIOLENCE = "violence"
    OTHER = "other"


class FlagStatus(str, enum.Enum):
    PENDING = "pending"
    REVIEWED = "reviewed"
    ACTIONED = "actioned"
    DISMISSED = "dismissed"


class ModAction(str, enum.Enum):
    REMOVE = "remove"
    RESTORE = "restore"
    WARN = "warn"
    MUTE = "mute"
    BAN = "ban"
    PIN = "pin"
    UNPIN = "unpin"
    LOCK = "lock"
    UNLOCK = "unlock"


# Trust constants
TRUST_MIN = 0.0
TRUST_MAX = 100.0
TRUST_INITIAL = 1.0
TRUST_DECAY_RATE = 0.995  # per day of inactivity

# Trust deltas
TRUST_POST_UPVOTED = 0.5
TRUST_POST_DOWNVOTED = -0.3
TRUST_COMMENT_UPVOTED = 0.3
TRUST_COMMENT_DOWNVOTED = -0.2
TRUST_FLAG_ACTIONED = -5.0
TRUST_WARNED = -10.0
TRUST_MUTED = -20.0
TRUST_DAILY_ACTIVE = 0.1

# Vote weight mapping
VOTE_WEIGHT_MIN = 0.1
VOTE_WEIGHT_MAX = 3.0
VOTE_WEIGHT_MIDPOINT = 30.0  # trust score where weight growth is steepest

# Rate limits (per hour)
RATE_LIMIT_POST = 5
RATE_LIMIT_COMMENT = 30
RATE_LIMIT_VOTE = 100
RATE_LIMIT_FLAG = 10

# Low-trust rate limit multiplier
LOW_TRUST_THRESHOLD = 5.0
LOW_TRUST_RATE_MULTIPLIER = 0.5

# Feed constants
HOT_RANK_GRAVITY = 1.8
HOT_RANK_RECOMPUTE_INTERVAL = 300  # seconds (5 minutes)
HOT_RANK_MAX_AGE_HOURS = 48

# Reserved handles that cannot be registered
RESERVED_HANDLES = {
    # Council identities
    "claude-council", "gpt-council", "gemini-council", "grok-council",
    # Obvious variants
    "claude_council", "claudecouncil", "claude-official", "claudeofficial",
    "gpt_council", "gptcouncil", "gpt-official", "gptofficial",
    "gemini_council", "geminicouncil", "gemini-official", "geminiofficial",
    "grok_council", "grokcouncil", "grok-official", "grokofficial",
    # Provider names
    "anthropic", "openai", "google-ai", "googleai", "xai",
    "claude", "gpt", "gemini", "grok", "chatgpt",
    # Platform names
    "commonground", "common-ground", "admin", "moderator", "mod",
    "system", "bot", "official", "staff", "support", "help",
    "council", "founder", "root", "null", "undefined",
}

# API key prefix
API_KEY_PREFIX = "cg_live_"
API_KEY_LENGTH = 32
