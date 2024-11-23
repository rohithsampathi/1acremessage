# message_processor.py

import os
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging
from tqdm import tqdm
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('message_processing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class Message:
    """Data class to represent a single message"""
    sender_name: str
    sender_id: Optional[str]
    content: str
    timestamp: datetime
    share_link: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict, participants_map: Dict[str, str]) -> Optional['Message']:
        """Create a Message instance from a dictionary"""
        try:
            # Basic validation
            if not isinstance(data, dict):
                return None
                
            # Get timestamp
            timestamp_ms = data.get('timestamp_ms')
            if not timestamp_ms:
                return None
            timestamp = datetime.fromtimestamp(timestamp_ms / 1000)
            
            # Get content and validate
            content = data.get('content', '').strip()
            if not content:
                # Check for share data
                share = data.get('share', {})
                if share and share.get('link'):
                    content = f"Shared link: {share['link']}"
                else:
                    return None
            
            # Skip system messages
            if any(skip_text in content.lower() for skip_text in [
                'quiet mode', 
                'notification', 
                'missed voice call',
                'missed video call',
                'started a video call',
                'started a voice call'
            ]):
                return None
            
            # Clean up sender name and get ID
            sender_name = data.get('sender_name', 'Unknown')
            sender_id = participants_map.get(sender_name)
            
            # Normalize 1acre sender names but keep original ID
            if 'acre' in sender_name.lower():
                sender_name = '1acre'
            
            return cls(
                sender_name=sender_name,
                sender_id=sender_id,
                content=content,
                timestamp=timestamp,
                share_link=share.get('link') if 'share' in data else None
            )
        except Exception as e:
            logger.error(f"Error creating message: {str(e)}, Data: {data}")
            return None

class MessageProcessor:
    """Process Instagram message JSON files"""
    
    @staticmethod
    def generate_unique_id(text: str) -> str:
        """Generate a short unique ID from text"""
        return hashlib.md5(text.encode()).hexdigest()[:8]
    
    @staticmethod
    def process_json_file(file_path: str) -> Optional[Dict]:
        """Process a single JSON file and return conversation data"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate basic structure
            if not isinstance(data, dict):
                logger.warning(f"Invalid JSON structure in {file_path}")
                return None
            
            messages = data.get('messages', [])
            if not messages:
                logger.warning(f"No messages found in {file_path}")
                return None
            
            # Extract participants and create ID mapping
            participants_map = {}
            for participant in data.get('participants', []):
                if isinstance(participant, dict):
                    name = participant.get('name', 'Unknown')
                    user_id = MessageProcessor.generate_unique_id(name)
                    participants_map[name] = user_id
            
            # Extract messages
            valid_messages = []
            for msg_data in messages:
                message = Message.from_dict(msg_data, participants_map)
                if message:
                    valid_messages.append(message)
            
            if not valid_messages:
                logger.warning(f"No valid messages found in {file_path}")
                return None
            
            # Get basic conversation info
            profile_name = data.get('title', 'Unknown User')
            thread_path = data.get('thread_path', '')
            
            # Format the conversation text
            conversation_text = []
            prev_sender = None
            for msg in sorted(valid_messages, key=lambda x: x.timestamp):
                if msg.sender_name != prev_sender:
                    sender_text = f"[{msg.sender_name} (ID: {msg.sender_id})]"
                    prev_sender = msg.sender_name
                else:
                    sender_text = "    "
                
                message_text = f"{sender_text}: {msg.content}"
                if msg.share_link:
                    message_text += f" (Link: {msg.share_link})"
                
                conversation_text.append(message_text)
            
            # Calculate timestamps
            first_contact = min(msg.timestamp for msg in valid_messages)
            last_contact = max(msg.timestamp for msg in valid_messages)
            
            return {
                'First Contact Date and Time': first_contact,
                'Last Contact Date and Time': last_contact,
                'Name of the Profile': profile_name,
                'Profile ID': MessageProcessor.generate_unique_id(profile_name),
                'Thread Path': thread_path,
                'Conversation': '\n'.join(conversation_text),
                'Message Count': len(valid_messages),
                'Conversation Length (Days)': (last_contact - first_contact).days + 1,
                'Participant Count': len(participants_map)
            }
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
            return None

    @staticmethod
    def find_json_files(folder_path: str) -> List[str]:
        """Find all message JSON files in the folder structure"""
        json_files = []
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file == 'message_1.json':
                    json_files.append(os.path.join(root, file))
        return json_files

    @staticmethod
    def process_folder(folder_path: str) -> pd.DataFrame:
        """Process all JSON files in a folder structure"""
        all_data = []
        
        # Find all JSON files
        json_files = MessageProcessor.find_json_files(folder_path)
        
        if not json_files:
            logger.warning(f"No JSON files found in {folder_path}")
            return pd.DataFrame()
        
        logger.info(f"Found {len(json_files)} conversation files to process")
        
        # Process files with progress bar
        with tqdm(total=len(json_files), desc="Processing conversations") as pbar:
            for file_path in json_files:
                conversation_data = MessageProcessor.process_json_file(file_path)
                if conversation_data:
                    all_data.append(conversation_data)
                pbar.update(1)
        
        if not all_data:
            logger.warning("No valid conversations found in any files")
            return pd.DataFrame()
            
        # Create DataFrame
        df = pd.DataFrame(all_data)
        
        # Sort by first contact date
        df.sort_values('First Contact Date and Time', ascending=False, inplace=True)
        
        return df

def main():
    """Main function to run the message processor"""
    try:
        input_folder = "./inbox1123/"
        output_file = "./instagram_conversations.xlsx"
        
        logger.info("Starting message processing...")
        df = MessageProcessor.process_folder(input_folder)
        
        if df.empty:
            logger.error("No valid conversations found")
            return
        
        # Save to Excel with optimized column widths
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Conversations')
        
        logger.info(f"Successfully processed {len(df)} conversations")
        logger.info(f"Data saved to {output_file}")
        
        # Print summary
        print("\nProcessing Summary:")
        print(f"Total conversations processed: {len(df)}")
        print(f"Date range: {df['First Contact Date and Time'].min()} to {df['Last Contact Date and Time'].max()}")
        print(f"Average messages per conversation: {df['Message Count'].mean():.1f}")
        print(f"Average conversation length: {df['Conversation Length (Days)'].mean():.1f} days")
        print(f"Total participants: {df['Participant Count'].sum()}")
        
    except Exception as e:
        logger.error(f"Error in main process: {str(e)}")

if __name__ == "__main__":
    main()