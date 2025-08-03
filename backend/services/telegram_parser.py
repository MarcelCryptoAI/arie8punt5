import re
import json
import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class TelegramSignalParser:
    """
    Robust parser for Telegram trading signals with multiple format support.
    Handles various signal providers and formats with intelligent pattern matching.
    """
    
    def __init__(self):
        # Common patterns for different signal elements
        self.coin_patterns = [
            r'#([A-Z]{3,6})/USDT',
            r'#([A-Z]{3,6})USDT',
            r'#([A-Z]{3,6})',
            r'\$([A-Z]{3,6})',
            r'([A-Z]{3,6})/USDT',
            r'([A-Z]{3,6})USDT',
            r'Coin[:\s]*([A-Z]{3,6})',
            r'Symbol[:\s]*([A-Z]{3,6})',
        ]
        
        self.position_patterns = [
            r'(?:Position|Direction|Type)[:\s]*(LONG|SHORT)',
            r'(LONG|SHORT)(?:\s+Position)?',
            r'#(LONG|SHORT)',
            r'📈\s*(LONG)',
            r'📉\s*(SHORT)',
        ]
        
        self.leverage_patterns = [
            r'Leverage[:\s]*(\d+)x?',
            r'Cross[:\s]*(\d+)x?',
            r'(\d+)x\s*Cross',
            r'(\d+)x\s*Leverage',
            r'Lev[:\s]*(\d+)',
        ]
        
        self.entry_patterns = [
            r'Entry[:\s]*([0-9,.]+(?:\s*-\s*[0-9,.]+)?)',
            r'Entry Zone[:\s]*([0-9,.]+(?:\s*-\s*[0-9,.]+)?)',
            r'Buy[:\s]*([0-9,.]+(?:\s*-\s*[0-9,.]+)?)',
            r'Enter[:\s]*([0-9,.]+(?:\s*-\s*[0-9,.]+)?)',
            r'Price[:\s]*([0-9,.]+(?:\s*-\s*[0-9,.]+)?)',
        ]
        
        self.target_patterns = [
            r'Target[s]?[:\s]*([0-9,.\s-]+)',
            r'TP[s]?[:\s]*([0-9,.\s-]+)',
            r'Take Profit[s]?[:\s]*([0-9,.\s-]+)',
            r'Sell[:\s]*([0-9,.\s-]+)',
        ]
        
        self.stoploss_patterns = [
            r'Stop Loss[:\s]*([0-9,.]+)',
            r'SL[:\s]*([0-9,.]+)',
            r'Stop[:\s]*([0-9,.]+)',
            r'Loss[:\s]*([0-9,.]+)',
        ]
    
    def parse_signal(self, text: str) -> Dict:
        """
        Parse a Telegram signal text and extract trading information.
        
        Args:
            text (str): Raw signal text
            
        Returns:
            Dict: Parsed signal data with extracted fields
        """
        try:
            # Clean and normalize text
            cleaned_text = self._clean_text(text)
            
            # Extract components
            coin = self._extract_coin(cleaned_text)
            position_type = self._extract_position_type(cleaned_text)
            leverage = self._extract_leverage(cleaned_text)
            entry_zones = self._extract_entry_zones(cleaned_text)
            targets = self._extract_targets(cleaned_text)
            stop_loss = self._extract_stop_loss(cleaned_text)
            
            # Determine if cross leverage is mentioned
            cross_leverage = self._detect_cross_leverage(cleaned_text)
            
            # Validate required fields
            errors = self._validate_signal(coin, position_type, entry_zones)
            
            result = {
                'raw_text': text,
                'coin': coin,
                'pair': 'USDT',  # Default to USDT
                'position_type': position_type,
                'entry_zones': entry_zones,
                'leverage': leverage,
                'cross_leverage': cross_leverage,
                'targets': targets,
                'stop_loss': stop_loss,
                'parse_errors': errors,
                'parsed_successfully': len(errors) == 0
            }
            
            logger.info(f"Parsed signal for {coin}: {position_type} @ {entry_zones}")
            return result
            
        except Exception as e:
            logger.error(f"Error parsing signal: {str(e)}")
            return {
                'raw_text': text,
                'parse_errors': [f"Parsing failed: {str(e)}"],
                'parsed_successfully': False
            }
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize signal text."""
        # Remove emojis but keep important trading symbols
        text = re.sub(r'[^\w\s#$/.:-]', ' ', text)
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip().upper()
    
    def _extract_coin(self, text: str) -> Optional[str]:
        """Extract coin symbol from text."""
        for pattern in self.coin_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                coin = match.group(1).upper()
                # Validate coin format (3-6 characters, alphabetic)
                if 3 <= len(coin) <= 6 and coin.isalpha():
                    return coin
        return None
    
    def _extract_position_type(self, text: str) -> Optional[str]:
        """Extract position type (LONG/SHORT) from text."""
        for pattern in self.position_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        return None
    
    def _extract_leverage(self, text: str) -> int:
        """Extract leverage from text, default to 1."""
        for pattern in self.leverage_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    leverage = int(match.group(1))
                    return min(max(leverage, 1), 100)  # Clamp between 1-100
                except ValueError:
                    continue
        return 1  # Default leverage
    
    def _extract_entry_zones(self, text: str) -> List[float]:
        """Extract entry zones from text."""
        entries = []
        
        for pattern in self.entry_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Handle ranges (e.g., "0.5-0.6" or "0.5 - 0.6")
                if '-' in match:
                    parts = match.split('-')
                    if len(parts) == 2:
                        try:
                            start = float(parts[0].strip().replace(',', ''))
                            end = float(parts[1].strip().replace(',', ''))
                            # Create 3 entry points in the range
                            step = (end - start) / 2
                            entries.extend([start, start + step, end])
                        except ValueError:
                            continue
                else:
                    # Single entry point
                    try:
                        entry = float(match.strip().replace(',', ''))
                        entries.append(entry)
                    except ValueError:
                        continue
        
        # Remove duplicates and sort
        entries = sorted(list(set(entries)))
        
        # If no entries found, try to extract numbers from the text
        if not entries:
            numbers = re.findall(r'\b\d+\.?\d*\b', text)
            for num in numbers:
                try:
                    val = float(num)
                    if 0.000001 < val < 1000000:  # Reasonable price range
                        entries.append(val)
                except ValueError:
                    continue
        
        return entries[:5]  # Limit to 5 entries max
    
    def _extract_targets(self, text: str) -> List[float]:
        """Extract target prices from text."""
        targets = []
        
        for pattern in self.target_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                target_text = match.group(1)
                # Extract all numbers from targets
                numbers = re.findall(r'\d+\.?\d*', target_text)
                for num in numbers:
                    try:
                        target = float(num)
                        if target > 0:
                            targets.append(target)
                    except ValueError:
                        continue
        
        # Remove duplicates and sort
        targets = sorted(list(set(targets)))
        return targets[:5]  # Limit to 5 targets max
    
    def _extract_stop_loss(self, text: str) -> Optional[float]:
        """Extract stop loss price from text."""
        for pattern in self.stoploss_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    sl = float(match.group(1).replace(',', ''))
                    return sl
                except ValueError:
                    continue
        return None
    
    def _detect_cross_leverage(self, text: str) -> bool:
        """Detect if cross leverage is mentioned."""
        cross_patterns = [
            r'CROSS',
            r'Cross Leverage',
            r'Cross Margin',
        ]
        
        for pattern in cross_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _validate_signal(self, coin: str, position_type: str, entry_zones: List[float]) -> List[str]:
        """Validate parsed signal and return list of errors."""
        errors = []
        
        if not coin:
            errors.append("No coin symbol found")
        
        if not position_type:
            errors.append("No position type (LONG/SHORT) found")
        
        if not entry_zones:
            errors.append("No entry zones found")
        
        return errors
    
    def batch_parse_signals(self, signals: List[str]) -> List[Dict]:
        """Parse multiple signals in batch."""
        results = []
        for signal_text in signals:
            result = self.parse_signal(signal_text)
            results.append(result)
        
        logger.info(f"Batch parsed {len(signals)} signals, {sum(1 for r in results if r['parsed_successfully'])} successful")
        return results
    
    def get_parsing_stats(self, results: List[Dict]) -> Dict:
        """Get statistics about parsing results."""
        total = len(results)
        successful = sum(1 for r in results if r.get('parsed_successfully', False))
        failed = total - successful
        
        error_types = {}
        for result in results:
            if not result.get('parsed_successfully', False):
                errors = result.get('parse_errors', [])
                for error in errors:
                    error_types[error] = error_types.get(error, 0) + 1
        
        return {
            'total_signals': total,
            'successful_parses': successful,
            'failed_parses': failed,
            'success_rate': (successful / total * 100) if total > 0 else 0,
            'common_errors': error_types
        }