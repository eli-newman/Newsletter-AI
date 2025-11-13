"""
Cost tracking for OpenAI API calls
Tracks token usage and costs per agent, per day
"""
import sqlite3
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from collections import defaultdict

# OpenAI pricing per 1K tokens (as of 2024)
# gpt-3.5-turbo pricing
PRICING = {
    "gpt-3.5-turbo": {
        "input": 0.0005,   # $0.50 per 1M tokens
        "output": 0.0015   # $1.50 per 1M tokens
    },
    "gpt-4": {
        "input": 0.03,     # $30 per 1M tokens
        "output": 0.06     # $60 per 1M tokens
    },
    "gpt-4-turbo": {
        "input": 0.01,     # $10 per 1M tokens
        "output": 0.03     # $30 per 1M tokens
    }
}

class CostTracker:
    """Track OpenAI API costs per agent and per day"""
    
    def __init__(self, db_path: str = "cache/cost_tracking.db"):
        """Initialize cost tracker"""
        self.db_path = db_path
        self.cache_dir = os.path.dirname(db_path) if os.path.dirname(db_path) else "cache"
        
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        
        self._init_db()
        self.daily_totals = defaultdict(lambda: {"input_tokens": 0, "output_tokens": 0, "cost": 0.0})
    
    def _init_db(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Daily cost tracking table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_costs
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 date TEXT NOT NULL,
                 agent TEXT NOT NULL,
                 model TEXT NOT NULL,
                 input_tokens INTEGER DEFAULT 0,
                 output_tokens INTEGER DEFAULT 0,
                 cost REAL DEFAULT 0.0,
                 calls INTEGER DEFAULT 1,
                 timestamp TEXT DEFAULT CURRENT_TIMESTAMP)
            """)
            
            # Create index for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_date_agent 
                ON daily_costs(date, agent)
            """)
            
            conn.commit()
    
    def _get_model_pricing(self, model: str) -> Dict[str, float]:
        """Get pricing for a model"""
        # Normalize model name
        model_lower = model.lower()
        if "gpt-4-turbo" in model_lower:
            return PRICING["gpt-4-turbo"]
        elif "gpt-4" in model_lower:
            return PRICING["gpt-4"]
        else:
            return PRICING["gpt-3.5-turbo"]  # Default
    
    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost based on token usage"""
        pricing = self._get_model_pricing(model)
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        return input_cost + output_cost
    
    def track_call(self, agent: str, model: str, input_tokens: int = 0, output_tokens: int = 0, 
                   usage: Optional[Dict] = None):
        """
        Track an API call
        
        Args:
            agent: Name of the agent (e.g., 'relevance', 'ranking')
            model: Model name (e.g., 'gpt-3.5-turbo')
            input_tokens: Input tokens used
            output_tokens: Output tokens used
            usage: Optional usage dict from OpenAI response (takes precedence)
        """
        if usage:
            input_tokens = usage.get("prompt_tokens", input_tokens)
            output_tokens = usage.get("completion_tokens", output_tokens)
        
        cost = self.calculate_cost(model, input_tokens, output_tokens)
        date = datetime.now().strftime("%Y-%m-%d")
        
        # Update daily totals
        key = f"{date}:{agent}"
        self.daily_totals[key]["input_tokens"] += input_tokens
        self.daily_totals[key]["output_tokens"] += output_tokens
        self.daily_totals[key]["cost"] += cost
        
        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO daily_costs 
                (date, agent, model, input_tokens, output_tokens, cost, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (date, agent, model, input_tokens, output_tokens, cost, datetime.now().isoformat()))
            conn.commit()
    
    def get_daily_cost(self, date: Optional[str] = None) -> Dict[str, Any]:
        """Get total cost for a specific date"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    agent,
                    model,
                    SUM(input_tokens) as total_input_tokens,
                    SUM(output_tokens) as total_output_tokens,
                    SUM(cost) as total_cost,
                    COUNT(*) as total_calls
                FROM daily_costs
                WHERE date = ?
                GROUP BY agent, model
                ORDER BY total_cost DESC
            """, (date,))
            
            results = cursor.fetchall()
            total_cost = sum(row[4] for row in results)
            
            return {
                "date": date,
                "total_cost": round(total_cost, 6),
                "by_agent": [
                    {
                        "agent": row[0],
                        "model": row[1],
                        "input_tokens": row[2],
                        "output_tokens": row[3],
                        "cost": round(row[4], 6),
                        "calls": row[5]
                    }
                    for row in results
                ]
            }
    
    def get_cost_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get cost summary for the last N days"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    date,
                    agent,
                    SUM(input_tokens) as total_input_tokens,
                    SUM(output_tokens) as total_output_tokens,
                    SUM(cost) as total_cost,
                    COUNT(*) as total_calls
                FROM daily_costs
                WHERE date >= date('now', '-' || ? || ' days')
                GROUP BY date, agent
                ORDER BY date DESC, total_cost DESC
            """, (days,))
            
            results = cursor.fetchall()
            
            # Group by date
            daily_summaries = defaultdict(lambda: {"agents": [], "total_cost": 0.0})
            
            for row in results:
                date, agent, input_tokens, output_tokens, cost, calls = row
                daily_summaries[date]["agents"].append({
                    "agent": agent,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cost": round(cost, 6),
                    "calls": calls
                })
                daily_summaries[date]["total_cost"] += cost
            
            # Format for display
            summary = []
            for date in sorted(daily_summaries.keys(), reverse=True):
                summary.append({
                    "date": date,
                    "total_cost": round(daily_summaries[date]["total_cost"], 6),
                    "by_agent": daily_summaries[date]["agents"]
                })
            
            total_all_days = sum(s["total_cost"] for s in summary)
            
            return {
                "period_days": days,
                "total_cost": round(total_all_days, 6),
                "daily_breakdown": summary
            }
    
    def print_daily_report(self, date: Optional[str] = None):
        """Print a formatted daily cost report"""
        report = self.get_daily_cost(date)
        
        print(f"\n💰 COST REPORT - {report['date']}")
        print("=" * 60)
        print(f"Total Cost: ${report['total_cost']:.6f}")
        print("-" * 60)
        
        if report['by_agent']:
            for agent_data in report['by_agent']:
                print(f"\n{agent_data['agent'].upper()}")
                print(f"  Model: {agent_data['model']}")
                print(f"  Calls: {agent_data['calls']}")
                print(f"  Input tokens: {agent_data['input_tokens']:,}")
                print(f"  Output tokens: {agent_data['output_tokens']:,}")
                print(f"  Cost: ${agent_data['cost']:.6f}")
        else:
            print("No API calls recorded for this date.")
        
        print("=" * 60)

# Global cost tracker instance
_cost_tracker: Optional[CostTracker] = None

def get_cost_tracker() -> CostTracker:
    """Get or create global cost tracker instance"""
    global _cost_tracker
    if _cost_tracker is None:
        _cost_tracker = CostTracker()
    return _cost_tracker

