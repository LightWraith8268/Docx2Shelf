"""
Community platform and collaboration system for Docx2Shelf.

This module provides community forums, knowledge sharing, contributor recognition,
and collaboration tools for the Docx2Shelf ecosystem.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse

import requests


@dataclass
class CommunityUser:
    """Community user profile."""

    user_id: str
    username: str
    display_name: str
    email: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None
    github_username: Optional[str] = None

    # Reputation and activity
    reputation_score: int = 0
    posts_count: int = 0
    contributions_count: int = 0
    helpful_answers: int = 0

    # Achievements and badges
    badges: List[str] = field(default_factory=list)
    achievements: List[str] = field(default_factory=list)

    # Timestamps
    joined_at: str = ""
    last_active: str = ""

    # Status
    is_verified: bool = False
    is_moderator: bool = False
    is_contributor: bool = False


@dataclass
class ForumPost:
    """Forum post or topic."""

    post_id: str
    author_id: str
    author_username: str
    title: str
    content: str
    category: str
    tags: List[str] = field(default_factory=list)

    # Thread information
    parent_id: Optional[str] = None  # For replies
    thread_id: str = ""
    is_pinned: bool = False
    is_locked: bool = False
    is_solved: bool = False

    # Engagement
    view_count: int = 0
    like_count: int = 0
    reply_count: int = 0

    # Timestamps
    created_at: str = ""
    updated_at: str = ""
    last_reply_at: str = ""


@dataclass
class KnowledgeArticle:
    """Community knowledge base article."""

    article_id: str
    title: str
    content: str
    summary: str
    author_id: str
    author_username: str
    category: str
    tags: List[str] = field(default_factory=list)

    # Status and quality
    status: str = "draft"  # draft, published, archived
    difficulty_level: str = "beginner"  # beginner, intermediate, advanced
    estimated_read_time: int = 0  # minutes

    # Engagement
    view_count: int = 0
    helpful_count: int = 0
    bookmark_count: int = 0

    # Versioning
    version: str = "1.0"
    last_reviewed: str = ""

    # Timestamps
    created_at: str = ""
    updated_at: str = ""


@dataclass
class ContributorActivity:
    """Tracks contributor activities and achievements."""

    user_id: str
    activity_type: str  # code, docs, support, plugin, tutorial
    activity_id: str
    title: str
    description: str
    points_earned: int = 0
    created_at: str = ""
    verified: bool = False


@dataclass
class Achievement:
    """Community achievement/badge definition."""

    achievement_id: str
    name: str
    description: str
    icon: str
    category: str
    requirements: Dict[str, Any] = field(default_factory=dict)
    points_value: int = 0
    rarity: str = "common"  # common, uncommon, rare, epic, legendary


class CommunityAchievementSystem:
    """Manages achievements and contributor recognition."""

    def __init__(self):
        self.achievements = self._load_achievements()

    def _load_achievements(self) -> Dict[str, Achievement]:
        """Load achievement definitions."""
        achievements = {
            "first_post": Achievement(
                achievement_id="first_post",
                name="First Steps",
                description="Made your first forum post",
                icon="💬",
                category="participation",
                requirements={"posts_count": 1},
                points_value=10
            ),
            "helpful_contributor": Achievement(
                achievement_id="helpful_contributor",
                name="Helpful Community Member",
                description="Received 10 helpful votes on answers",
                icon="🤝",
                category="helpfulness",
                requirements={"helpful_answers": 10},
                points_value=50
            ),
            "plugin_author": Achievement(
                achievement_id="plugin_author",
                name="Plugin Creator",
                description="Published a plugin to the marketplace",
                icon="🔌",
                category="development",
                requirements={"plugins_published": 1},
                points_value=100
            ),
            "documentation_writer": Achievement(
                achievement_id="documentation_writer",
                name="Documentation Expert",
                description="Contributed to documentation",
                icon="📚",
                category="documentation",
                requirements={"docs_contributions": 5},
                points_value=75
            ),
            "community_leader": Achievement(
                achievement_id="community_leader",
                name="Community Leader",
                description="Reached 1000 reputation points",
                icon="👑",
                category="reputation",
                requirements={"reputation_score": 1000},
                points_value=200,
                rarity="rare"
            ),
            "bug_hunter": Achievement(
                achievement_id="bug_hunter",
                name="Bug Hunter",
                description="Reported 5 verified bugs",
                icon="🐛",
                category="quality",
                requirements={"bugs_reported": 5},
                points_value=60
            ),
            "tutorial_master": Achievement(
                achievement_id="tutorial_master",
                name="Tutorial Master",
                description="Created 3 helpful tutorials",
                icon="🎓",
                category="education",
                requirements={"tutorials_created": 3},
                points_value=120
            )
        }
        return achievements

    def check_achievements(self, user: CommunityUser, activities: List[ContributorActivity]) -> List[str]:
        """Check which new achievements a user has earned."""
        user_stats = self._calculate_user_stats(user, activities)
        new_achievements = []

        for achievement_id, achievement in self.achievements.items():
            if achievement_id not in user.achievements:
                if self._meets_requirements(user_stats, achievement.requirements):
                    new_achievements.append(achievement_id)

        return new_achievements

    def _calculate_user_stats(self, user: CommunityUser, activities: List[ContributorActivity]) -> Dict[str, int]:
        """Calculate user statistics for achievement checking."""
        stats = {
            "posts_count": user.posts_count,
            "helpful_answers": user.helpful_answers,
            "reputation_score": user.reputation_score,
            "contributions_count": user.contributions_count
        }

        # Count specific activity types
        for activity in activities:
            activity_type = activity.activity_type
            stat_key = f"{activity_type}_count"
            stats[stat_key] = stats.get(stat_key, 0) + 1

        # Special calculations
        stats["plugins_published"] = sum(1 for a in activities if a.activity_type == "plugin")
        stats["docs_contributions"] = sum(1 for a in activities if a.activity_type == "docs")
        stats["tutorials_created"] = sum(1 for a in activities if a.activity_type == "tutorial")
        stats["bugs_reported"] = sum(1 for a in activities if a.activity_type == "bug_report")

        return stats

    def _meets_requirements(self, user_stats: Dict[str, int], requirements: Dict[str, Any]) -> bool:
        """Check if user meets achievement requirements."""
        for req_key, req_value in requirements.items():
            if user_stats.get(req_key, 0) < req_value:
                return False
        return True


class CommunityForums:
    """Community forums and discussion platform."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize forums database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS forum_posts (
                    post_id TEXT PRIMARY KEY,
                    author_id TEXT NOT NULL,
                    author_username TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    category TEXT NOT NULL,
                    tags TEXT NOT NULL,
                    parent_id TEXT,
                    thread_id TEXT NOT NULL,
                    is_pinned BOOLEAN DEFAULT FALSE,
                    is_locked BOOLEAN DEFAULT FALSE,
                    is_solved BOOLEAN DEFAULT FALSE,
                    view_count INTEGER DEFAULT 0,
                    like_count INTEGER DEFAULT 0,
                    reply_count INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_reply_at TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS forum_categories (
                    category_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    color TEXT DEFAULT '#3498db',
                    post_count INTEGER DEFAULT 0,
                    is_default BOOLEAN DEFAULT FALSE
                )
            """)

            # Insert default categories
            default_categories = [
                ("general", "General Discussion", "General questions and discussions", "#3498db", True),
                ("help", "Help & Support", "Get help with Docx2Shelf", "#e74c3c", False),
                ("plugins", "Plugin Development", "Plugin development discussions", "#9b59b6", False),
                ("feature-requests", "Feature Requests", "Suggest new features", "#f39c12", False),
                ("showcase", "Showcase", "Show off your projects", "#2ecc71", False),
                ("announcements", "Announcements", "Official announcements", "#34495e", False)
            ]

            for cat_id, name, desc, color, is_default in default_categories:
                conn.execute("""
                    INSERT OR IGNORE INTO forum_categories VALUES (?, ?, ?, ?, 0, ?)
                """, (cat_id, name, desc, color, is_default))

    def create_post(self, post: ForumPost) -> bool:
        """Create a new forum post."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO forum_posts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    post.post_id, post.author_id, post.author_username, post.title,
                    post.content, post.category, json.dumps(post.tags), post.parent_id,
                    post.thread_id, post.is_pinned, post.is_locked, post.is_solved,
                    post.view_count, post.like_count, post.reply_count,
                    post.created_at, post.updated_at, post.last_reply_at
                ))

                # Update category post count
                conn.execute("""
                    UPDATE forum_categories
                    SET post_count = post_count + 1
                    WHERE category_id = ?
                """, (post.category,))

            return True
        except Exception as e:
            print(f"Failed to create post: {e}")
            return False

    def get_posts(self, category: str = "", limit: int = 20, offset: int = 0) -> List[ForumPost]:
        """Get forum posts with optional filtering."""
        with sqlite3.connect(self.db_path) as conn:
            sql = "SELECT * FROM forum_posts"
            params = []

            if category:
                sql += " WHERE category = ?"
                params.append(category)

            sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor = conn.execute(sql, params)
            posts = []

            for row in cursor.fetchall():
                post = ForumPost(
                    post_id=row[0], author_id=row[1], author_username=row[2],
                    title=row[3], content=row[4], category=row[5],
                    tags=json.loads(row[6]), parent_id=row[7], thread_id=row[8],
                    is_pinned=row[9], is_locked=row[10], is_solved=row[11],
                    view_count=row[12], like_count=row[13], reply_count=row[14],
                    created_at=row[15], updated_at=row[16], last_reply_at=row[17]
                )
                posts.append(post)

            return posts

    def search_posts(self, query: str, category: str = "") -> List[ForumPost]:
        """Search forum posts."""
        with sqlite3.connect(self.db_path) as conn:
            sql = """
                SELECT * FROM forum_posts
                WHERE (title LIKE ? OR content LIKE ?)
            """
            params = [f"%{query}%", f"%{query}%"]

            if category:
                sql += " AND category = ?"
                params.append(category)

            sql += " ORDER BY created_at DESC LIMIT 50"

            cursor = conn.execute(sql, params)
            posts = []

            for row in cursor.fetchall():
                post = ForumPost(
                    post_id=row[0], author_id=row[1], author_username=row[2],
                    title=row[3], content=row[4], category=row[5],
                    tags=json.loads(row[6]), parent_id=row[7], thread_id=row[8],
                    is_pinned=row[9], is_locked=row[10], is_solved=row[11],
                    view_count=row[12], like_count=row[13], reply_count=row[14],
                    created_at=row[15], updated_at=row[16], last_reply_at=row[17]
                )
                posts.append(post)

            return posts


class KnowledgeBase:
    """Community knowledge base system."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize knowledge base database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_articles (
                    article_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    author_id TEXT NOT NULL,
                    author_username TEXT NOT NULL,
                    category TEXT NOT NULL,
                    tags TEXT NOT NULL,
                    status TEXT DEFAULT 'draft',
                    difficulty_level TEXT DEFAULT 'beginner',
                    estimated_read_time INTEGER DEFAULT 0,
                    view_count INTEGER DEFAULT 0,
                    helpful_count INTEGER DEFAULT 0,
                    bookmark_count INTEGER DEFAULT 0,
                    version TEXT DEFAULT '1.0',
                    last_reviewed TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

    def create_article(self, article: KnowledgeArticle) -> bool:
        """Create a new knowledge base article."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO knowledge_articles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    article.article_id, article.title, article.content, article.summary,
                    article.author_id, article.author_username, article.category,
                    json.dumps(article.tags), article.status, article.difficulty_level,
                    article.estimated_read_time, article.view_count, article.helpful_count,
                    article.bookmark_count, article.version, article.last_reviewed,
                    article.created_at, article.updated_at
                ))
            return True
        except Exception as e:
            print(f"Failed to create article: {e}")
            return False

    def search_articles(self, query: str = "", category: str = "",
                       difficulty: str = "") -> List[KnowledgeArticle]:
        """Search knowledge base articles."""
        with sqlite3.connect(self.db_path) as conn:
            sql = "SELECT * FROM knowledge_articles WHERE status = 'published'"
            params = []

            if query:
                sql += " AND (title LIKE ? OR content LIKE ? OR summary LIKE ?)"
                query_param = f"%{query}%"
                params.extend([query_param, query_param, query_param])

            if category:
                sql += " AND category = ?"
                params.append(category)

            if difficulty:
                sql += " AND difficulty_level = ?"
                params.append(difficulty)

            sql += " ORDER BY helpful_count DESC, view_count DESC LIMIT 50"

            cursor = conn.execute(sql, params)
            articles = []

            for row in cursor.fetchall():
                article = KnowledgeArticle(
                    article_id=row[0], title=row[1], content=row[2], summary=row[3],
                    author_id=row[4], author_username=row[5], category=row[6],
                    tags=json.loads(row[7]), status=row[8], difficulty_level=row[9],
                    estimated_read_time=row[10], view_count=row[11], helpful_count=row[12],
                    bookmark_count=row[13], version=row[14], last_reviewed=row[15],
                    created_at=row[16], updated_at=row[17]
                )
                articles.append(article)

            return articles


class CommunityPlatform:
    """Main community platform interface."""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or Path.home() / ".docx2shelf" / "community"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.db_path = self.data_dir / "community.db"

        self.forums = CommunityForums(self.db_path)
        self.knowledge_base = KnowledgeBase(self.db_path)
        self.achievement_system = CommunityAchievementSystem()

        self._init_user_database()

    def _init_user_database(self):
        """Initialize user management database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS community_users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    display_name TEXT NOT NULL,
                    email TEXT,
                    bio TEXT,
                    avatar_url TEXT,
                    website TEXT,
                    location TEXT,
                    github_username TEXT,
                    reputation_score INTEGER DEFAULT 0,
                    posts_count INTEGER DEFAULT 0,
                    contributions_count INTEGER DEFAULT 0,
                    helpful_answers INTEGER DEFAULT 0,
                    badges TEXT NOT NULL DEFAULT '[]',
                    achievements TEXT NOT NULL DEFAULT '[]',
                    joined_at TEXT NOT NULL,
                    last_active TEXT NOT NULL,
                    is_verified BOOLEAN DEFAULT FALSE,
                    is_moderator BOOLEAN DEFAULT FALSE,
                    is_contributor BOOLEAN DEFAULT FALSE
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS contributor_activities (
                    activity_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    activity_type TEXT NOT NULL,
                    activity_ref_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    points_earned INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    verified BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (user_id) REFERENCES community_users (user_id)
                )
            """)

    def create_user(self, user: CommunityUser) -> bool:
        """Create a new community user."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO community_users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user.user_id, user.username, user.display_name, user.email,
                    user.bio, user.avatar_url, user.website, user.location,
                    user.github_username, user.reputation_score, user.posts_count,
                    user.contributions_count, user.helpful_answers,
                    json.dumps(user.badges), json.dumps(user.achievements),
                    user.joined_at, user.last_active, user.is_verified,
                    user.is_moderator, user.is_contributor
                ))
            return True
        except Exception as e:
            print(f"Failed to create user: {e}")
            return False

    def get_user(self, user_id: str) -> Optional[CommunityUser]:
        """Get user by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM community_users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()

            if row:
                return CommunityUser(
                    user_id=row[0], username=row[1], display_name=row[2], email=row[3],
                    bio=row[4], avatar_url=row[5], website=row[6], location=row[7],
                    github_username=row[8], reputation_score=row[9], posts_count=row[10],
                    contributions_count=row[11], helpful_answers=row[12],
                    badges=json.loads(row[13]), achievements=json.loads(row[14]),
                    joined_at=row[15], last_active=row[16], is_verified=row[17],
                    is_moderator=row[18], is_contributor=row[19]
                )

        return None

    def record_activity(self, activity: ContributorActivity) -> bool:
        """Record a contributor activity."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO contributor_activities VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    activity.activity_id, activity.user_id, activity.activity_type,
                    activity.activity_id, activity.title, activity.description,
                    activity.points_earned, activity.created_at, activity.verified
                ))

                # Update user statistics
                conn.execute("""
                    UPDATE community_users
                    SET contributions_count = contributions_count + 1,
                        reputation_score = reputation_score + ?
                    WHERE user_id = ?
                """, (activity.points_earned, activity.user_id))

            return True
        except Exception as e:
            print(f"Failed to record activity: {e}")
            return False

    def get_leaderboard(self, metric: str = "reputation", limit: int = 20) -> List[CommunityUser]:
        """Get community leaderboard."""
        order_by = {
            "reputation": "reputation_score DESC",
            "posts": "posts_count DESC",
            "contributions": "contributions_count DESC",
            "helpful": "helpful_answers DESC"
        }.get(metric, "reputation_score DESC")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(f"""
                SELECT * FROM community_users
                ORDER BY {order_by}
                LIMIT ?
            """, (limit,))

            users = []
            for row in cursor.fetchall():
                user = CommunityUser(
                    user_id=row[0], username=row[1], display_name=row[2], email=row[3],
                    bio=row[4], avatar_url=row[5], website=row[6], location=row[7],
                    github_username=row[8], reputation_score=row[9], posts_count=row[10],
                    contributions_count=row[11], helpful_answers=row[12],
                    badges=json.loads(row[13]), achievements=json.loads(row[14]),
                    joined_at=row[15], last_active=row[16], is_verified=row[17],
                    is_moderator=row[18], is_contributor=row[19]
                )
                users.append(user)

            return users


def create_community_platform(data_dir: Optional[Path] = None) -> CommunityPlatform:
    """Create a configured community platform instance."""
    return CommunityPlatform(data_dir)