"""
Onigiri Icon Registry — Thư viện icon trung tâm
================================================
Cung cấp icon chuẩn (Lucide/Feather style) dùng trong toàn bộ add-on.
Dễ dàng tham chiếu theo tên, thay đổi icon không làm vỡ cấu trúc.

Sử dụng:
    from .icon_registry import get_icon, get_icon_url, ICON_CATEGORIES
    url = get_icon_url("github")  # → data:image/svg+xml;base64,...
"""

import base64
import os
from typing import Optional, Dict, List

# ═══════════════════════════════════════════════════════════════
# CATEGORIES
# ═══════════════════════════════════════════════════════════════

ICON_CATEGORIES = {
    "social": "🌐 Mạng xã hội",
    "messaging": "💬 Nhắn tin & Giao tiếp",
    "tech": "💻 Công nghệ & Dev",
    "media": "🎬 Giải trí & Media",
    "ui": "🖱️ Giao diện người dùng",
    "action": "⚡ Hành động",
    "navigation": "🧭 Điều hướng",
    "file": "📁 File & Dữ liệu",
    "commerce": "🛒 Thương mại",
    "security": "🔒 Bảo mật",
    "communication": "📢 Truyền thông",
    "general": "📦 Chung",
}

# ═══════════════════════════════════════════════════════════════
# SVG ICON LIBRARY — ~60+ icons chuẩn thế giới
# Mỗi icon: viewBox 0 0 24 24, stroke-width 2, Lucide style
# ═══════════════════════════════════════════════════════════════

_ICONS: Dict[str, dict] = {
    # ── 🌐 SOCIAL MEDIA ──────────────────────────────────────
    "facebook": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"/></svg>',
        "category": "social",
        "aliases": ["fb", "meta"],
    },
    "twitter": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 4s-.7 2.1-2 3.4c1.6 10-9.4 17.3-18 11.6 2.2.1 4.4-.6 6-2C3 15.5.5 9.6 3 5c2.2 2.6 5.6 4.1 9 4-.9-4.2 4-6.6 7-3.8 1.1 0 3-1.2 3-1.2z"/></svg>',
        "category": "social",
        "aliases": ["x", "xcom"],
    },
    "instagram": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="20" rx="5" ry="5"/><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/><line x1="17.5" y1="6.5" x2="17.51" y2="6.5"/></svg>',
        "category": "social",
        "aliases": ["ig", "insta"],
    },
    "youtube": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22.54 6.42a2.78 2.78 0 0 0-1.94-2C18.88 4 12 4 12 4s-6.88 0-8.6.46a2.78 2.78 0 0 0-1.94 2A29.94 29.94 0 0 0 1 12a29.94 29.94 0 0 0 .46 5.58 2.78 2.78 0 0 0 1.94 2C5.12 20 12 20 12 20s6.88 0 8.6-.46a2.78 2.78 0 0 0 1.94-2A29.94 29.94 0 0 0 23 12a29.94 29.94 0 0 0-.46-5.58z"/><polygon points="9.75 15.02 15.5 12 9.75 8.98 9.75 15.02"/></svg>',
        "category": "social",
        "aliases": ["yt"],
    },
    "tiktok": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 12a4 4 0 1 0 4 4V4a5 5 0 0 0 5 5"/></svg>',
        "category": "social",
        "aliases": [],
    },
    "linkedin": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"/><rect x="2" y="9" width="4" height="12"/><circle cx="4" cy="4" r="2"/></svg>',
        "category": "social",
        "aliases": ["li"],
    },
    "github": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"/></svg>',
        "category": "tech",
        "aliases": ["gh"],
    },
    "discord": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="12" r="1"/><circle cx="15" cy="12" r="1"/><path d="M7.5 7.5c3.5-1 5.5-1 9 0"/><path d="M7.5 16.5c3.5 1 5.5 1 9 0"/><path d="M15.5 22c-2 0-3-1-3-3H7c0-4 0-14 0-14h10s0 10 0 14h-1.5"/></svg>',
        "category": "social",
        "aliases": [],
    },
    "reddit": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M16.5 15a5 5 0 0 1-9 0"/><circle cx="9" cy="10" r="1"/><circle cx="15" cy="10" r="1"/><path d="M12 2a3 3 0 0 0-3 3"/><path d="M17 4a2 2 0 0 0-2 2"/></svg>',
        "category": "social",
        "aliases": [],
    },
    "pinterest": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="m12 2 2 4-2 4"/><path d="M8 2h8"/><path d="M8 22h8"/></svg>',
        "category": "social",
        "aliases": [],
    },
    "snapchat": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a4 4 0 0 1 4 4v2h2a2 2 0 0 1 2 2v1a2 2 0 0 1-2 2h-1a9 9 0 0 1-10 0H6a2 2 0 0 1-2-2v-1a2 2 0 0 1 2-2h2V6a4 4 0 0 1 4-4z"/></svg>',
        "category": "social",
        "aliases": [],
    },

    # ── 💬 MESSAGING ─────────────────────────────────────────
    "whatsapp": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 11.5a8.38 8.38 0 0 1-1.3 4.5A8.5 8.5 0 0 1 3 16.29l-2 5 5.1-1.7A8.5 8.5 0 0 1 21 11.5z"/><path d="M9 10h.01"/><path d="M12 10h.01"/><path d="M15 10h.01"/></svg>',
        "category": "messaging",
        "aliases": ["wa"],
    },
    "telegram": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.5 2.5 2.5 10l6 3 4-4 4 4 3-6-6 12-3-4"/></svg>',
        "category": "messaging",
        "aliases": ["tg"],
    },
    "messenger": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>',
        "category": "messaging",
        "aliases": ["chat", "message"],
    },

    # ── 💻 TECH & DEV ────────────────────────────────────────
    "gitlab": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m22 13.3-4.7-14.5L12 6.5 6.7-1.2 2 13.3 12 22.8z"/></svg>',
        "category": "tech",
        "aliases": [],
    },
    "stackoverflow": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 17v4H7v-4"/><path d="M7 10h10l-1 6H8z"/><path d="M9 3h6l-1 4H10z"/><path d="M10.5 20h3"/></svg>',
        "category": "tech",
        "aliases": ["so"],
    },
    "npm": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="8" width="20" height="8" rx="1"/><rect x="2" y="8" width="6" height="8"/></svg>',
        "category": "tech",
        "aliases": [],
    },
    "docker": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="8" width="20" height="10" rx="2"/><path d="M2 13h20"/><rect x="5" y="4" width="3" height="3"/><rect x="9" y="4" width="3" height="3"/><rect x="13" y="2" width="3" height="3"/></svg>',
        "category": "tech",
        "aliases": [],
    },
    "figma": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 12a4 4 0 1 1 8 0 4 4 0 0 1-8 0z"/><path d="M4 20a4 4 0 0 1 4-4h4v4a4 4 0 0 1-8 0z"/><path d="M12 4v8h4a4 4 0 0 0 0-8h-4z"/><path d="M8 4a4 4 0 0 0 0 8h4V4H8z"/></svg>',
        "category": "tech",
        "aliases": [],
    },
    "notion": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M7 7h3l4 10h3M14 7l-4 10"/></svg>',
        "category": "tech",
        "aliases": [],
    },
    "slack": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="8" width="5" height="8" rx="1"/><rect x="8" y="14" width="8" height="5" rx="1"/><rect x="14" y="8" width="5" height="8" rx="1"/><rect x="8" y="2" width="8" height="5" rx="1"/></svg>',
        "category": "tech",
        "aliases": [],
    },
    "vscode": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m17.5 2-14 7 5 5-5 5 14 7V2z"/><path d="m8.5 12 9-5v10l-9-5z"/></svg>',
        "category": "tech",
        "aliases": ["code", "ide"],
    },

    # ── 🎬 MEDIA & ENTERTAINMENT ─────────────────────────────
    "spotify": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M8 11.5c3-1 6-1 8 0"/><path d="M9 14.5c2-.7 4-.7 6 0"/><path d="M10 8.5c2-.5 3.5-.5 5 0"/></svg>',
        "category": "media",
        "aliases": ["music"],
    },
    "twitch": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v12h5v4l4-4h4l5-5V3H3zm4 4h2v4H7zm5 0h2v4h-2z"/></svg>',
        "category": "media",
        "aliases": [],
    },
    "steam": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="8" cy="12" r="2"/><path d="M14 12h4"/><path d="M10 6v4"/></svg>',
        "category": "media",
        "aliases": ["game"],
    },
    "netflix": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="4" width="8" height="16"/><rect x="14" y="4" width="8" height="16"/><line x1="10" y1="10" x2="14" y2="10"/><line x1="10" y1="15" x2="14" y2="15"/></svg>',
        "category": "media",
        "aliases": [],
    },

    # ── 🖱️ UI ELEMENTS ───────────────────────────────────────
    "home": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>',
        "category": "ui",
        "aliases": [],
    },
    "user": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
        "category": "ui",
        "aliases": ["profile", "avatar", "person"],
    },
    "users": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
        "category": "ui",
        "aliases": ["group", "community"],
    },
    "settings": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>',
        "category": "ui",
        "aliases": ["gear", "cog", "preferences"],
    },
    "bell": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>',
        "category": "ui",
        "aliases": ["notification", "alert"],
    },
    "search": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
        "category": "ui",
        "aliases": ["magnifying-glass", "find"],
    },
    "menu": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg>',
        "category": "ui",
        "aliases": ["hamburger", "burger", "nav"],
    },
    "xmark": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
        "category": "ui",
        "aliases": ["close", "x", "cancel"],
    },
    "check": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
        "category": "ui",
        "aliases": ["tick", "done", "success"],
    },
    "plus": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>',
        "category": "ui",
        "aliases": ["add", "new", "create"],
    },
    "minus": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/></svg>',
        "category": "ui",
        "aliases": ["remove", "delete"],
    },
    "heart": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>',
        "category": "ui",
        "aliases": ["like", "favorite", "love"],
    },
    "star": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
        "category": "ui",
        "aliases": ["favourite", "rating"],
    },
    "bookmark": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m19 21-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg>',
        "category": "ui",
        "aliases": ["save"],
    },

    # ── ⚡ ACTIONS ────────────────────────────────────────────
    "share": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>',
        "category": "action",
        "aliases": ["send"],
    },
    "download": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>',
        "category": "action",
        "aliases": [],
    },
    "upload": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>',
        "category": "action",
        "aliases": [],
    },
    "refresh": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>',
        "category": "action",
        "aliases": ["sync", "reload", "update"],
    },
    "edit": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>',
        "category": "action",
        "aliases": ["pencil", "write"],
    },
    "trash": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>',
        "category": "action",
        "aliases": ["delete", "remove", "bin"],
    },
    "copy": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>',
        "category": "action",
        "aliases": ["duplicate", "clone"],
    },
    "link": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>',
        "category": "action",
        "aliases": ["chain", "url", "hyperlink"],
    },

    # ── 🧭 NAVIGATION ─────────────────────────────────────────
    "chevron-left": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>',
        "category": "navigation",
        "aliases": ["arrow-left", "back", "previous"],
    },
    "chevron-right": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>',
        "category": "navigation",
        "aliases": ["arrow-right", "forward", "next"],
    },
    "chevron-up": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="18 15 12 9 6 15"/></svg>',
        "category": "navigation",
        "aliases": ["arrow-up", "up"],
    },
    "chevron-down": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>',
        "category": "navigation",
        "aliases": ["arrow-down", "down", "expand"],
    },
    "external-link": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>',
        "category": "navigation",
        "aliases": ["open", "new-tab"],
    },

    # ── 📁 FILE & DATA ────────────────────────────────────────
    "file": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/></svg>',
        "category": "file",
        "aliases": ["document", "page"],
    },
    "folder": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>',
        "category": "file",
        "aliases": ["directory"],
    },
    "image": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>',
        "category": "file",
        "aliases": ["picture", "photo"],
    },
    "film": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18"/><line x1="7" y1="2" x2="7" y2="22"/><line x1="17" y1="2" x2="17" y2="22"/><line x1="2" y1="12" x2="22" y2="12"/><line x1="2" y1="7" x2="7" y2="7"/><line x1="2" y1="17" x2="7" y2="17"/><line x1="17" y1="7" x2="22" y2="7"/><line x1="17" y1="17" x2="22" y2="17"/></svg>',
        "category": "file",
        "aliases": ["video", "movie"],
    },
    "music": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg>',
        "category": "file",
        "aliases": ["audio", "sound"],
    },

    # ── 🛒 COMMERCE ───────────────────────────────────────────
    "shopping-cart": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/></svg>',
        "category": "commerce",
        "aliases": ["cart", "buy", "purchase"],
    },
    "credit-card": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>',
        "category": "commerce",
        "aliases": ["payment", "card"],
    },
    "tag": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/><line x1="7" y1="7" x2="7.01" y2="7"/></svg>',
        "category": "commerce",
        "aliases": ["label", "price"],
    },

    # ── 🔒 SECURITY ───────────────────────────────────────────
    "lock": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>',
        "category": "security",
        "aliases": ["secure", "encrypted"],
    },
    "unlock": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 9.9-1"/></svg>',
        "category": "security",
        "aliases": ["open-lock"],
    },
    "shield": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
        "category": "security",
        "aliases": ["security", "protection"],
    },
    "eye": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>',
        "category": "security",
        "aliases": ["view", "visible", "show"],
    },
    "eye-off": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>',
        "category": "security",
        "aliases": ["hide", "invisible", "hidden"],
    },

    # ── 📢 COMMUNICATION ──────────────────────────────────────
    "mail": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>',
        "category": "communication",
        "aliases": ["email", "gmail", "envelope"],
    },
    "phone": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>',
        "category": "communication",
        "aliases": ["call", "telephone"],
    },
    "globe": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>',
        "category": "communication",
        "aliases": ["web", "internet", "world", "language"],
    },
    "map-pin": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>',
        "category": "communication",
        "aliases": ["location", "marker", "pin", "map"],
    },

    # ── 📦 GENERAL ────────────────────────────────────────────
    "calendar": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>',
        "category": "general",
        "aliases": ["date", "event", "schedule"],
    },
    "clock": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
        "category": "general",
        "aliases": ["time", "history"],
    },
    "camera": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>',
        "category": "general",
        "aliases": ["photo-camera"],
    },
    "info": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
        "category": "general",
        "aliases": ["information", "help", "about"],
    },
    "palette": {
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="13.5" cy="6.5" r="1.5"/><circle cx="17.5" cy="10.5" r="1.5"/><circle cx="8.5" cy="7.5" r="1.5"/><circle cx="6.5" cy="12.5" r="1.5"/><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.93 0 1.5-.67 1.5-1.5 0-.39-.15-.74-.39-1.01-.23-.26-.38-.61-.38-.99 0-.83.67-1.5 1.5-1.5H16c3.31 0 6-2.69 6-6 0-5.5-4.5-10-10-10z"/></svg>',
        "category": "general",
        "aliases": ["color", "theme", "paint"],
    },
}

# ═══════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════

def _build_alias_map() -> Dict[str, str]:
    """Build a mapping from aliases → canonical icon name."""
    alias_map = {}
    for name, data in _ICONS.items():
        alias_map[name] = name
        for alias in data.get("aliases", []):
            if alias not in alias_map:
                alias_map[alias] = name
    return alias_map

_ALIAS_MAP = _build_alias_map()

def get_icon(name: str) -> Optional[dict]:
    """
    Lấy icon data theo tên hoặc alias.
    
    Args:
        name: Tên icon hoặc alias (vd: "github", "gh", "settings", "gear")
    
    Returns:
        dict với keys: svg, category, aliases — hoặc None nếu không tìm thấy
    """
    canonical = _ALIAS_MAP.get(name.lower())
    if canonical:
        return _ICONS[canonical]
    return None

def get_icon_svg(name: str) -> Optional[str]:
    """Lấy raw SVG string của icon."""
    icon = get_icon(name)
    return icon["svg"] if icon else None

def get_icon_url(name: str, color: str = "currentColor") -> str:
    """
    Lấy data URI cho icon (dùng trong CSS mask-image hoặc <img>).
    
    Args:
        name: Tên icon hoặc alias
        color: Màu stroke (chỉ dùng nếu muốn override, mặc định currentColor)
    
    Returns:
        Chuỗi data URI: "data:image/svg+xml;base64,..."
    """
    svg = get_icon_svg(name)
    if not svg:
        return ""
    # Inject color if needed
    if color != "currentColor":
        svg = svg.replace('stroke="currentColor"', f'stroke="{color}"')
    b64 = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    return f"data:image/svg+xml;base64,{b64}"

def get_icon_css_url(name: str) -> str:
    """
    Trả về url() cho CSS mask-image.
    Dùng: mask-image: url('...');
    """
    url = get_icon_url(name)
    return f"url('{url}')" if url else ""

def list_icons(category: str = None) -> List[str]:
    """
    Liệt kê tất cả icon, có thể lọc theo category.
    
    Args:
        category: Key trong ICON_CATEGORIES hoặc None để lấy tất cả
    """
    if category:
        return sorted([n for n, d in _ICONS.items() if d["category"] == category])
    return sorted(_ICONS.keys())

def list_categories() -> Dict[str, str]:
    """Trả về dict categories {key: label}."""
    return dict(ICON_CATEGORIES)

def get_icons_by_category() -> Dict[str, List[str]]:
    """Trả về dict {category_key: [icon_names]}."""
    result = {}
    for name, data in _ICONS.items():
        cat = data["category"]
        if cat not in result:
            result[cat] = []
        result[cat].append(name)
    return result

# ═══════════════════════════════════════════════════════════════
# BACKWARD COMPATIBILITY: Map system icon names → registry icons
# ═══════════════════════════════════════════════════════════════

SYSTEM_ICON_MAP = {
    "add": "plus",
    "browse": "menu",
    "stats": "bar-chart",  # fallback
    "sync": "refresh",
    "settings": "settings",
    "star": "star",
    "edit": "edit",
    "focus": "eye",
    "more": "menu",
    "folder": "folder",
    "book": "file",
    "options": "settings",
    "get_shared": "download",
    "create_deck": "plus",
    "import_file": "upload",
    "filtered_deck": "filter",
    "collapse_closed": "chevron-right",
    "collapse_open": "chevron-down",
    "subdeck": "folder",
    "deck": "file",
}
