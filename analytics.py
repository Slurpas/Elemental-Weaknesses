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
            "pokemon_views": {},  # Track actual Pokemon viewed (not search terms)
            "battles": 0,
            "leagues": {},
            "hourly_usage": defaultdict(int),
            "hourly_stats": defaultdict(lambda: {
                "visits": 0,
                "pokemon_views": 0,
                "battles": 0,
                "unique_visitors": set()
            }),
            "daily_usage": {},
            "start_date": datetime.now().isoformat(),
            "last_reset": datetime.now().isoformat()
        }
    
    def save_data(self):
        """Save analytics data to file"""
        try:
            with self.lock:
                # Convert sets to lists for JSON serialization
                data_to_save = self.data.copy()
                for hour, stats in data_to_save["hourly_stats"].items():
                    if isinstance(stats, dict) and "unique_visitors" in stats:
                        stats["unique_visitors"] = list(stats["unique_visitors"])
                
                with open(self.data_file, 'w') as f:
                    json.dump(data_to_save, f, indent=2, default=str)
        except Exception as e:
            print(f"[ANALYTICS] Error saving data: {e}")
    
    def track_visit(self, ip_address, user_agent=""):
        """Track a unique visitor"""
        today = datetime.now().strftime("%Y-%m-%d")
        hour = datetime.now().strftime("%H")
        
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
            self.data["hourly_usage"][hour] += 1
            
            # Track detailed hourly statistics
            if hour not in self.data["hourly_stats"]:
                self.data["hourly_stats"][hour] = {
                    "visits": 0,
                    "pokemon_views": 0,
                    "battles": 0,
                    "unique_visitors": set()
                }
            
            self.data["hourly_stats"][hour]["visits"] += 1
            self.data["hourly_stats"][hour]["unique_visitors"].add(ip_address)
            
            # Increment page views
            self.data["page_views"] += 1
        
        # Save data periodically (not on every request to avoid performance issues)
        if self.data["page_views"] % 10 == 0:  # Save every 10 page views
            self.save_data()
    
    def track_search(self, search_term):
        """Track search terms (what users type)"""
        with self.lock:
            if search_term not in self.data["searches"]:
                self.data["searches"][search_term] = 0
            self.data["searches"][search_term] += 1
    
    def track_pokemon_view(self, pokemon_name):
        """Track when a Pokemon is actually viewed (not just searched for)"""
        hour = datetime.now().strftime("%H")
        
        with self.lock:
            # Track Pokemon views
            if pokemon_name not in self.data["pokemon_views"]:
                self.data["pokemon_views"][pokemon_name] = 0
            self.data["pokemon_views"][pokemon_name] += 1
            
            # Track in hourly stats
            if hour not in self.data["hourly_stats"]:
                self.data["hourly_stats"][hour] = {
                    "visits": 0,
                    "pokemon_views": 0,
                    "battles": 0,
                    "unique_visitors": set()
                }
            
            self.data["hourly_stats"][hour]["pokemon_views"] += 1
    
    def track_battle(self, league):
        """Track battle simulations"""
        hour = datetime.now().strftime("%H")
        
        with self.lock:
            self.data["battles"] += 1
            
            if league not in self.data["leagues"]:
                self.data["leagues"][league] = 0
            self.data["leagues"][league] += 1
            
            # Track in hourly stats
            if hour not in self.data["hourly_stats"]:
                self.data["hourly_stats"][hour] = {
                    "visits": 0,
                    "pokemon_views": 0,
                    "battles": 0,
                    "unique_visitors": set()
                }
            
            self.data["hourly_stats"][hour]["battles"] += 1
    
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
        try:
            with self.lock:
                # Ensure all required fields exist with defaults
                if "visitors" not in self.data:
                    self.data["visitors"] = {}
                if "searches" not in self.data:
                    self.data["searches"] = {}
                if "pokemon_views" not in self.data:
                    self.data["pokemon_views"] = {}
                if "leagues" not in self.data:
                    self.data["leagues"] = {}
                if "hourly_usage" not in self.data:
                    self.data["hourly_usage"] = defaultdict(int)
                if "hourly_stats" not in self.data:
                    self.data["hourly_stats"] = defaultdict(lambda: {
                        "visits": 0,
                        "pokemon_views": 0,
                        "battles": 0,
                        "unique_visitors": set()
                    })
                if "daily_usage" not in self.data:
                    self.data["daily_usage"] = {}
                if "page_views" not in self.data:
                    self.data["page_views"] = 0
                if "battles" not in self.data:
                    self.data["battles"] = 0
                if "start_date" not in self.data:
                    self.data["start_date"] = datetime.now().isoformat()
                
                # Calculate unique visitors (IPs that visited in last 30 days)
                thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
                recent_visitors = sum(1 for visitor in self.data["visitors"].values() 
                                    if visitor.get("last_visit", "") >= thirty_days_ago)
                
                # Get top searches (what users type)
                top_searches = sorted(self.data["searches"].items(), 
                                    key=lambda x: x[1], reverse=True)[:10]
                
                # Get top Pokemon views (actual Pokemon viewed)
                top_pokemon_views = sorted(self.data["pokemon_views"].items(), 
                                         key=lambda x: x[1], reverse=True)[:10]
                
                # Get top leagues
                top_leagues = sorted(self.data["leagues"].items(), 
                                   key=lambda x: x[1], reverse=True)
                
                # Get peak usage hour
                if self.data["hourly_usage"]:
                    peak_hour = max(self.data["hourly_usage"].items(), 
                                  key=lambda x: x[1])
                else:
                    peak_hour = ("00", 0)
                
                # Get recent daily usage (last 7 days)
                recent_daily = {}
                for i in range(7):
                    date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
                    recent_daily[date] = self.data["daily_usage"].get(date, 0)
                
                # Get hourly statistics for the last 24 hours
                hourly_stats = {}
                for i in range(24):
                    hour = f"{(datetime.now() - timedelta(hours=i)).hour:02d}"
                    if hour in self.data["hourly_stats"]:
                        stats = self.data["hourly_stats"][hour]
                        hourly_stats[hour] = {
                            "visits": stats.get("visits", 0),
                            "pokemon_views": stats.get("pokemon_views", 0),
                            "battles": stats.get("battles", 0),
                            "unique_visitors": len(stats.get("unique_visitors", set()))
                        }
                    else:
                        hourly_stats[hour] = {
                            "visits": 0,
                            "pokemon_views": 0,
                            "battles": 0,
                            "unique_visitors": 0
                        }
                
                return {
                    "total_visitors": len(self.data["visitors"]),
                    "recent_visitors": recent_visitors,
                    "total_page_views": self.data["page_views"],
                    "total_battles": self.data["battles"],
                    "top_searches": top_searches,
                    "top_pokemon_views": top_pokemon_views,  # New: actual Pokemon viewed
                    "top_leagues": top_leagues,
                    "peak_hour": peak_hour,
                    "recent_daily": recent_daily,
                    "hourly_stats": hourly_stats,  # New: detailed hourly breakdown
                    "start_date": self.data["start_date"],
                    "current_concurrent": len(self.data["visitors"])  # Rough estimate
                }
        except Exception as e:
            print(f"[ANALYTICS] Error in get_stats: {e}")
            # Return safe default values
            return {
                "total_visitors": 0,
                "recent_visitors": 0,
                "total_page_views": 0,
                "total_battles": 0,
                "top_searches": [],
                "top_pokemon_views": [],
                "top_leagues": [],
                "peak_hour": ("00", 0),
                "recent_daily": {},
                "hourly_stats": {},
                "start_date": datetime.now().isoformat(),
                "current_concurrent": 0
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