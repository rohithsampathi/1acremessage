# components/metrics.py

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

class MetricsAnalyzer:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
    
    def get_overview_metrics(self):
        """Calculate main dashboard metrics"""
        return {
            'total_conversations': len(self.df),
            'total_messages': int(self.df['Message Count'].sum()),
            'avg_length': f"{self.df['Conversation Length (Days)'].mean():.1f}",
            'active_conversations': len(
                self.df[self.df['Last Contact Date and Time'] >= (datetime.now() - timedelta(days=7))]
            )
        }
    
    def create_timeline_chart(self):
        """Create conversation timeline visualization"""
        try:
            daily_conv = (
                self.df.groupby(self.df['First Contact Date and Time'].dt.date)
                .size()
                .reset_index(name='count')
            )
            
            fig = px.line(
                daily_conv, 
                x='First Contact Date and Time', 
                y='count',
                title='Daily Conversation Volume'
            )
            
            fig.update_layout(
                template='plotly_dark',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis_title="Date",
                yaxis_title="Number of Conversations"
            )
            
            return fig
        except Exception as e:
            print(f"Error creating timeline chart: {str(e)}")
            return go.Figure()
    
    def create_activity_heatmap(self):
        """Create activity heatmap by hour and day"""
        try:
            # Create hour and day columns
            activity_df = self.df.copy()
            activity_df['hour'] = activity_df['First Contact Date and Time'].dt.hour
            activity_df['day'] = activity_df['First Contact Date and Time'].dt.dayofweek
            
            # Calculate average messages for each hour-day combination
            activity = (
                activity_df.groupby(['hour', 'day'])['Message Count']
                .mean()
                .reset_index()
            )
            
            # Create the pivot table for the heatmap
            pivot_table = activity.pivot(
                index='day',
                columns='hour',
                values='Message Count'
            ).fillna(0)
            
            # Create heatmap
            fig = go.Figure(data=go.Heatmap(
                z=pivot_table.values,
                x=[f"{hour:02d}:00" for hour in range(24)],
                y=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                colorscale='Viridis'
            ))
            
            fig.update_layout(
                title='Message Activity Heatmap',
                template='plotly_dark',
                height=400,
                xaxis_title="Hour of Day",
                yaxis_title="Day of Week"
            )
            
            return fig
        except Exception as e:
            print(f"Error creating heatmap: {str(e)}")
            return go.Figure()
    
    def create_conversation_length_chart(self):
        """Create conversation length distribution chart"""
        try:
            fig = px.histogram(
                self.df,
                x='Conversation Length (Days)',
                nbins=30,
                title='Conversation Length Distribution'
            )
            
            fig.update_layout(
                template='plotly_dark',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis_title="Length (Days)",
                yaxis_title="Number of Conversations"
            )
            
            return fig
        except Exception as e:
            print(f"Error creating length chart: {str(e)}")
            return go.Figure()