import json
import time
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import threading
import os
import hashlib

class Analytics:
    def __init__(self, data_file="analytics_data.json"):
        self.data_file = data_file
        self.lock = threading.Lock()
        self.data = self.load_data()
        # Track unique battles: {session_key: last_timestamp}
        self.unique_battles = {}  # Not persisted, in-memory only
        
    def load_data(self):
        """Load analytics data from file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    # Ensure hourly_usage is a defaultdict(int)
                    if "hourly_usage" in data:
                        data["hourly_usage"] = defaultdict(int, data["hourly_usage"])
                    return data
        except Exception as e:
            print(f"[ANALYTICS] Error loading data: {e}")
        
        # Return default structure if file doesn't exist or is corrupted
        return {
            "visitors": {},
            "page_views": 0,
            "searches": {},
            "battles": 0,
            "leagues": {},
            "hourly_usage": defaultdict(int),
            "daily_usage": {},
            "start_date": datetime.now().isoformat(),
            "last_reset": datetime.now().isoformat()
        }
    
    def save_data(self):
        """Save analytics data to file"""
        try:
            with self.lock:
                with open(self.data_file, 'w') as f:
                    json.dump(self.data, f, indent=2, default=str)
        except Exception as e:
            print(f"[ANALYTICS] Error saving data: {e}")
    
    def track_visit(self, ip_address, user_agent=""):
        """Track a unique visitor"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        with self.lock:
            # Track unique visitors by IP
            if ip_address not in self.data["visitors"]:
                self.data["visitors"][ip_address] = {
                    "first_visit": today,
                    "last_visit": today,
                    "visit_count": 0
                }
            
            self.data["visitors"][ip_address]["last_visit"] = today
            self.data["visitors"][ip_address]["visit_count"] += 1
            
            # Track daily usage
            if today not in self.data["daily_usage"]:
                self.data["daily_usage"][today] = 0
            self.data["daily_usage"][today] += 1
            
            # Track hourly usage
            hour = datetime.now().strftime("%H")
            self.data["hourly_usage"][hour] += 1
            
            # Increment page views
            self.data["page_views"] += 1
        
        # Save data periodically (not on every request to avoid performance issues)
        if self.data["page_views"] % 10 == 0:  # Save every 10 page views
            self.save_data()
    
    def track_search(self, pokemon_name):
        """Track Pokemon searches"""
        with self.lock:
            if pokemon_name not in self.data["searches"]:
                self.data["searches"][pokemon_name] = 0
            self.data["searches"][pokemon_name] += 1
    
    def track_battle(self, league):
        """Track battle simulations"""
        with self.lock:
            self.data["battles"] += 1
            
            if league not in self.data["leagues"]:
                self.data["leagues"][league] = 0
            self.data["leagues"][league] += 1
    
    def track_unique_battle(self, team, team_moves, opponent, opponent_moves, league, ip=None, window_minutes=5):
        """
        Track a unique full-team-vs-opponent battle (with moves and league).
        Only count if not seen in the last window_minutes.
        """
        if len(team) != 3 or not opponent:
            return False  # Only count full teams
        # Build a session key: sorted team, moves, opponent, opponent moves, league
        def moves_key(moves):
            # moves: dict with keys 'fast', 'charged1', 'charged2'
            return tuple((k, moves.get(k, '')) for k in sorted(moves.keys()))
        team_key = tuple(sorted((pid, tuple(sorted(team_moves.get(pid, {}).items()))) for pid in team))
        opponent_key = (opponent, tuple(sorted(opponent_moves.items())) if opponent_moves else ())
        session_key = (team_key, opponent_key, league)
        # Hash for memory efficiency
        session_hash = hashlib.sha256(str(session_key).encode()).hexdigest()
        now = time.time()
        with self.lock:
            last_time = self.unique_battles.get(session_hash, 0)
            if now - last_time > window_minutes * 60:
                self.unique_battles[session_hash] = now
                self.data["battles"] += 1
                return True
        return False
    
    def get_stats(self):
        """Get current analytics statistics"""
        with self.lock:
            # Calculate unique visitors (IPs that visited in last 30 days)
            thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            recent_visitors = sum(1 for visitor in self.data["visitors"].values() 
                                if visitor["last_visit"] >= thirty_days_ago)
            
            # Get top searches
            top_searches = sorted(self.data["searches"].items(), 
                                key=lambda x: x[1], reverse=True)[:10]
            
            # Get top leagues
            top_leagues = sorted(self.data["leagues"].items(), 
                               key=lambda x: x[1], reverse=True)
            
            # Get peak usage hour
            peak_hour = max(self.data["hourly_usage"].items(), 
                          key=lambda x: x[1]) if self.data["hourly_usage"] else ("00", 0)
            
            # Get recent daily usage (last 7 days)
            recent_daily = {}
            for i in range(7):
                date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
                recent_daily[date] = self.data["daily_usage"].get(date, 0)
            
            return {
                "total_visitors": len(self.data["visitors"]),
                "recent_visitors": recent_visitors,
                "total_page_views": self.data["page_views"],
                "total_battles": self.data["battles"],
                "top_searches": top_searches,
                "top_leagues": top_leagues,
                "peak_hour": peak_hour,
                "recent_daily": recent_daily,
                "start_date": self.data["start_date"],
                "current_concurrent": len(self.data["visitors"])  # Rough estimate
            }
    
    def cleanup_old_data(self, days_to_keep=90):
        """Clean up old visitor data to keep file size manageable"""
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).strftime("%Y-%m-%d")
        
        with self.lock:
            # Remove old visitors
            old_visitors = [ip for ip, data in self.data["visitors"].items() 
                          if data["last_visit"] < cutoff_date]
            for ip in old_visitors:
                del self.data["visitors"][ip]
            
            # Remove old daily usage data
            old_days = [day for day in self.data["daily_usage"].keys() 
                       if day < cutoff_date]
            for day in old_days:
                del self.data["daily_usage"][day]
        
        self.save_data()
        print(f"[ANALYTICS] Cleaned up {len(old_visitors)} old visitors and {len(old_days)} old days")

# Global analytics instance
analytics = Analytics()

# Schedule periodic cleanup (every 30 days)
import atexit
from datetime import datetime, timedelta

def cleanup_old_data():
    """Clean up old analytics data to keep file size manageable"""
    try:
        analytics.cleanup_old_data(days_to_keep=90)  # Keep 90 days of data
    except Exception as e:
        print(f"[ANALYTICS] Error during cleanup: {e}")

# Register cleanup function to run on exit
atexit.register(cleanup_old_data) 