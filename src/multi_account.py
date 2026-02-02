"""
Multi-Account Manager - Birden fazla bot oturumunu yönetir
"""
import threading
from dataclasses import dataclass
from typing import Dict, Optional, Callable

@dataclass
class BotSession:
    """Tek bir bot oturumunu temsil eder"""
    session_id: str
    name: str
    bot_instance: object  # BotCore
    monitor: dict
    is_active: bool = False
    stats: dict = None
    
    def __post_init__(self):
        if self.stats is None:
            self.stats = {"caught": 0, "missed": 0, "casts": 0}

class MultiAccountManager:
    """Birden fazla hesap/bot yöneticisi"""
    
    def __init__(self):
        self.sessions: Dict[str, BotSession] = {}
        self.active_session_id: Optional[str] = None
        self.on_session_change: Optional[Callable] = None
        self._session_counter = 0
    
    def create_session(self, name: str, bot_instance, monitor: dict) -> str:
        """Yeni oturum oluştur"""
        self._session_counter += 1
        session_id = f"session_{self._session_counter}"
        
        session = BotSession(
            session_id=session_id,
            name=name,
            bot_instance=bot_instance,
            monitor=monitor.copy() if monitor else {"top": 0, "left": 0, "width": 800, "height": 600}
        )
        
        self.sessions[session_id] = session
        
        # İlk oturum ise aktif yap
        if len(self.sessions) == 1:
            self.active_session_id = session_id
        
        return session_id
    
    def remove_session(self, session_id: str) -> bool:
        """Oturumu kaldır"""
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        
        # Çalışıyorsa durdur
        if session.is_active and session.bot_instance:
            session.bot_instance.stop()
        
        del self.sessions[session_id]
        
        # Aktif oturum silindiyse başka birini seç
        if self.active_session_id == session_id:
            if self.sessions:
                self.active_session_id = list(self.sessions.keys())[0]
            else:
                self.active_session_id = None
        
        return True
    
    def get_session(self, session_id: str) -> Optional[BotSession]:
        """Oturumu getir"""
        return self.sessions.get(session_id)
    
    def get_active_session(self) -> Optional[BotSession]:
        """Aktif oturumu getir"""
        if self.active_session_id:
            return self.sessions.get(self.active_session_id)
        return None
    
    def set_active_session(self, session_id: str) -> bool:
        """Aktif oturumu değiştir"""
        if session_id in self.sessions:
            self.active_session_id = session_id
            if self.on_session_change:
                self.on_session_change(session_id)
            return True
        return False
    
    def start_session(self, session_id: str) -> bool:
        """Belirtilen oturumu başlat"""
        session = self.sessions.get(session_id)
        if session and session.bot_instance:
            session.bot_instance.monitor = session.monitor
            session.bot_instance.start()
            session.is_active = True
            return True
        return False
    
    def stop_session(self, session_id: str) -> bool:
        """Belirtilen oturumu durdur"""
        session = self.sessions.get(session_id)
        if session and session.bot_instance:
            session.bot_instance.stop()
            session.is_active = False
            return True
        return False
    
    def start_all(self):
        """Tüm oturumları başlat"""
        for session_id in self.sessions:
            self.start_session(session_id)
    
    def stop_all(self):
        """Tüm oturumları durdur"""
        for session_id in self.sessions:
            self.stop_session(session_id)
    
    def get_all_stats(self) -> dict:
        """Tüm oturumların istatistiklerini topla"""
        total = {"caught": 0, "missed": 0, "casts": 0, "active_count": 0}
        
        for session in self.sessions.values():
            if session.bot_instance:
                stats = session.bot_instance.stats
                total["caught"] += stats.get("caught", 0)
                total["missed"] += stats.get("missed", 0)
                total["casts"] += stats.get("casts", 0)
                if session.is_active:
                    total["active_count"] += 1
        
        return total
    
    def list_sessions(self) -> list:
        """Oturum listesini döndür"""
        result = []
        for sid, session in self.sessions.items():
            result.append({
                "id": sid,
                "name": session.name,
                "is_active": session.is_active,
                "caught": session.bot_instance.stats["caught"] if session.bot_instance else 0
            })
        return result
    
    @property
    def session_count(self) -> int:
        return len(self.sessions)
    
    @property
    def active_count(self) -> int:
        return sum(1 for s in self.sessions.values() if s.is_active)
