import openai
import anthropic
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
import os

logger = logging.getLogger(__name__)

class AIOptimizer:
    """
    AI-powered optimization service for trading parameters and strategies.
    Supports multiple AI providers (OpenAI, Anthropic) for analysis and recommendations.
    """
    
    def __init__(self, provider: str = 'openai', model: str = 'gpt-4'):
        self.provider = provider.lower()
        self.model = model
        
        # Initialize AI client based on provider
        if self.provider == 'openai':
            openai.api_key = os.environ.get('OPENAI_API_KEY')
            self.client = openai
        elif self.provider == 'anthropic':
            self.client = anthropic.Anthropic(
                api_key=os.environ.get('ANTHROPIC_API_KEY')
            )
        else:
            raise ValueError(f"Unsupported AI provider: {provider}")
    
    def analyze_performance(self, backtest_data: Dict, optimization_type: str = 'parameters') -> Dict:
        """
        Analyze backtest performance and provide optimization recommendations.
        
        Args:
            backtest_data: Complete backtest results and trade history
            optimization_type: Type of optimization (parameters, strategy, risk_management)
            
        Returns:
            Dict: Analysis results with recommendations
        """
        try:
            # Prepare analysis prompt based on optimization type
            prompt = self._create_analysis_prompt(backtest_data, optimization_type)
            
            # Get AI response
            ai_response = self._get_ai_response(prompt)
            
            if ai_response:
                # Parse AI recommendations
                recommendations = self._parse_recommendations(ai_response, optimization_type)
                
                return {
                    'success': True,
                    'prompt': prompt,
                    'response': ai_response,
                    'recommendations': recommendations,
                    'confidence_score': self._calculate_confidence(ai_response),
                    'expected_improvement': self._estimate_improvement(recommendations, backtest_data),
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to get AI response'
                }
                
        except Exception as e:
            logger.error(f"Error in AI analysis: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def optimize_settings(self, performance_data: List[Dict], 
                         current_settings: Dict, optimization_goals: List[str]) -> Dict:
        """
        Optimize trading settings based on historical performance data.
        
        Args:
            performance_data: List of backtest results with settings
            current_settings: Current trading settings
            optimization_goals: List of optimization objectives
            
        Returns:
            Dict: Optimization results with recommendations
        """
        try:
            prompt = self._create_optimization_prompt(
                performance_data, current_settings, optimization_goals
            )
            
            ai_response = self._get_ai_response(prompt)
            
            if ai_response:
                recommendations = self._parse_settings_recommendations(ai_response)
                
                return {
                    'success': True,
                    'prompt': prompt,
                    'response': ai_response,
                    'recommendations': recommendations,
                    'confidence_score': self._calculate_confidence(ai_response),
                    'expected_improvement': self._estimate_settings_improvement(recommendations),
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to get AI optimization response'
                }
                
        except Exception as e:
            logger.error(f"Error in settings optimization: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_trading_suggestions(self, recent_performance: List[Dict], 
                              current_settings: Dict) -> Dict:
        """
        Get general trading suggestions based on recent performance.
        
        Args:
            recent_performance: Recent backtest results
            current_settings: Current trading configuration
            
        Returns:
            Dict: Trading suggestions and recommendations
        """
        try:
            prompt = self._create_suggestions_prompt(recent_performance, current_settings)
            
            ai_response = self._get_ai_response(prompt)
            
            if ai_response:
                suggestions = self._parse_suggestions(ai_response)
                
                return {
                    'success': True,
                    'suggestions': suggestions,
                    'confidence': self._calculate_confidence(ai_response),
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to generate suggestions'
                }
                
        except Exception as e:
            logger.error(f"Error generating suggestions: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def analyze_market_conditions(self, coins: List[str]) -> Dict:
        """
        Analyze current market conditions for given coins.
        
        Args:
            coins: List of coin symbols to analyze
            
        Returns:
            Dict: Market analysis and trading recommendations
        """
        try:
            prompt = self._create_market_analysis_prompt(coins)
            
            ai_response = self._get_ai_response(prompt)
            
            if ai_response:
                analysis = self._parse_market_analysis(ai_response)
                
                return {
                    'success': True,
                    'analysis': analysis,
                    'recommendations': analysis.get('recommendations', []),
                    'sentiment': analysis.get('sentiment', 'neutral'),
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to analyze market conditions'
                }
                
        except Exception as e:
            logger.error(f"Error in market analysis: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_ai_response(self, prompt: str) -> Optional[str]:
        """Get response from AI provider."""
        try:
            if self.provider == 'openai':
                response = self.client.ChatCompletion.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an expert cryptocurrency trading analyst and optimizer."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=2000,
                    temperature=0.7
                )
                return response.choices[0].message.content
                
            elif self.provider == 'anthropic':
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=2000,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                return response.content[0].text
                
        except Exception as e:
            logger.error(f"Error getting AI response: {str(e)}")
            return None
    
    def _create_analysis_prompt(self, backtest_data: Dict, optimization_type: str) -> str:
        """Create analysis prompt for AI."""
        results = backtest_data['results']
        trade_history = backtest_data.get('trade_history', [])
        settings = backtest_data.get('settings_used', {})
        
        prompt = f"""
Analyze the following trading backtest results and provide optimization recommendations:

BACKTEST RESULTS:
- Total PnL: {results.get('total_pnl_percentage', 0):.2f}%
- Win Rate: {results.get('win_rate', 0):.2f}%
- Total Trades: {results.get('total_trades', 0)}
- Max Drawdown: {results.get('max_drawdown', 0):.2f}%
- Sharpe Ratio: {results.get('sharpe_ratio', 0):.2f}

CURRENT SETTINGS:
- Default Leverage: {settings.get('default_leverage', 1)}
- Risk Percentage: {settings.get('risk_percentage', 2.0)}%
- Entry Steps: {settings.get('entry_steps', 3)}
- Entry Distribution: {settings.get('entry_distribution', [40, 35, 25])}
- Target Distribution: {settings.get('target_distribution', [50, 30, 20])}

OPTIMIZATION TYPE: {optimization_type}

Please provide specific recommendations to improve performance. Focus on:
1. Parameter adjustments for better risk/reward
2. Entry and exit strategy improvements
3. Risk management optimization
4. Expected impact of each recommendation

Format your response as JSON with the following structure:
{{
    "analysis": "Detailed analysis of current performance",
    "recommendations": {{
        "parameter_name": new_value,
        "another_parameter": new_value
    }},
    "reasoning": "Explanation for each recommendation",
    "expected_improvement": "Estimated improvement percentage",
    "confidence": "Confidence level (0-1)"
}}
"""
        return prompt
    
    def _create_optimization_prompt(self, performance_data: List[Dict], 
                                  current_settings: Dict, optimization_goals: List[str]) -> str:
        """Create optimization prompt for AI."""
        prompt = f"""
Optimize trading settings based on the following historical performance data:

CURRENT SETTINGS:
{json.dumps(current_settings, indent=2)}

HISTORICAL PERFORMANCE:
"""
        for i, data in enumerate(performance_data):
            results = data['results']
            prompt += f"""
Backtest {i+1}:
- PnL: {results.get('total_pnl_percentage', 0):.2f}%
- Win Rate: {results.get('win_rate', 0):.2f}%
- Max Drawdown: {results.get('max_drawdown', 0):.2f}%
"""
        
        prompt += f"""
OPTIMIZATION GOALS: {', '.join(optimization_goals)}

Please provide optimized settings that would improve performance based on the historical data.
Focus on finding the best balance between the specified goals.

Return your response as JSON with optimized parameter values:
{{
    "optimized_settings": {{
        "parameter_name": new_value
    }},
    "reasoning": "Explanation for the optimizations",
    "expected_improvement": estimated_improvement_percentage,
    "confidence": confidence_level
}}
"""
        return prompt
    
    def _create_suggestions_prompt(self, recent_performance: List[Dict], 
                                 current_settings: Dict) -> str:
        """Create suggestions prompt for AI."""
        prompt = f"""
Provide trading improvement suggestions based on recent performance:

RECENT PERFORMANCE:
"""
        for i, result in enumerate(recent_performance):
            prompt += f"""
Backtest {i+1}: PnL: {result.get('total_pnl_percentage', 0):.2f}%, Win Rate: {result.get('win_rate', 0):.2f}%
"""
        
        prompt += f"""
CURRENT SETTINGS:
{json.dumps(current_settings, indent=2)}

Provide actionable suggestions for improvement. Include:
1. Market condition adaptations
2. Risk management improvements  
3. Entry/exit timing optimizations
4. General trading strategy advice

Format as JSON:
{{
    "suggestions": [
        {{
            "category": "risk_management|strategy|timing|market_adaptation",
            "title": "Suggestion title",
            "description": "Detailed description",
            "priority": "high|medium|low",
            "implementation": "How to implement this suggestion"
        }}
    ],
    "summary": "Overall assessment and key insights"
}}
"""
        return prompt
    
    def _create_market_analysis_prompt(self, coins: List[str]) -> str:
        """Create market analysis prompt for AI."""
        prompt = f"""
Analyze current market conditions for the following cryptocurrencies: {', '.join(coins)}

Please provide:
1. Overall market sentiment analysis
2. Individual coin assessments
3. Trading recommendations based on current conditions
4. Risk factors to consider
5. Optimal strategy suggestions for current market

Format your response as JSON:
{{
    "market_sentiment": "bullish|bearish|neutral|uncertain",
    "overall_analysis": "General market assessment",
    "coin_analysis": {{
        "COIN": {{
            "sentiment": "bullish|bearish|neutral",
            "key_factors": ["factor1", "factor2"],
            "recommendation": "buy|sell|hold|avoid"
        }}
    }},
    "recommendations": [
        {{
            "action": "Recommended action",
            "reasoning": "Why this action is recommended",
            "timeframe": "short|medium|long term"
        }}
    ],
    "risk_factors": ["factor1", "factor2"],
    "strategy_suggestions": ["suggestion1", "suggestion2"]
}}

Note: Base your analysis on general market principles and technical analysis concepts.
"""
        return prompt
    
    def _parse_recommendations(self, ai_response: str, optimization_type: str) -> Dict:
        """Parse AI response into structured recommendations."""
        try:
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                parsed = json.loads(json_str)
                return parsed.get('recommendations', {})
            else:
                # Fallback: create basic recommendations
                return self._create_fallback_recommendations(optimization_type)
                
        except Exception as e:
            logger.error(f"Error parsing AI recommendations: {str(e)}")
            return self._create_fallback_recommendations(optimization_type)
    
    def _parse_settings_recommendations(self, ai_response: str) -> Dict:
        """Parse AI response for settings optimization."""
        try:
            import re
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                parsed = json.loads(json_str)
                return parsed.get('optimized_settings', {})
            else:
                return {}
        except Exception as e:
            logger.error(f"Error parsing settings recommendations: {str(e)}")
            return {}
    
    def _parse_suggestions(self, ai_response: str) -> List[Dict]:
        """Parse AI response for trading suggestions."""
        try:
            import re
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                parsed = json.loads(json_str)
                return parsed.get('suggestions', [])
            else:
                return []
        except Exception as e:
            logger.error(f"Error parsing suggestions: {str(e)}")
            return []
    
    def _parse_market_analysis(self, ai_response: str) -> Dict:
        """Parse AI response for market analysis."""
        try:
            import re
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            else:
                return {'sentiment': 'neutral', 'analysis': 'Unable to parse market analysis'}
        except Exception as e:
            logger.error(f"Error parsing market analysis: {str(e)}")
            return {'sentiment': 'neutral', 'analysis': f'Error: {str(e)}'}
    
    def _calculate_confidence(self, ai_response: str) -> float:
        """Calculate confidence score based on AI response."""
        # Simple confidence calculation based on response length and keywords
        confidence_keywords = ['confident', 'strong', 'clear', 'significant', 'highly']
        uncertainty_keywords = ['uncertain', 'might', 'possibly', 'unclear', 'difficult']
        
        response_lower = ai_response.lower()
        confidence_count = sum(1 for word in confidence_keywords if word in response_lower)
        uncertainty_count = sum(1 for word in uncertainty_keywords if word in response_lower)
        
        base_confidence = 0.5
        confidence_boost = confidence_count * 0.1
        uncertainty_penalty = uncertainty_count * 0.1
        
        return max(0.1, min(1.0, base_confidence + confidence_boost - uncertainty_penalty))
    
    def _estimate_improvement(self, recommendations: Dict, backtest_data: Dict) -> float:
        """Estimate potential improvement from recommendations."""
        # Simple estimation based on number and type of recommendations
        improvement_factors = {
            'default_leverage': 5.0,
            'risk_percentage': 3.0,
            'entry_distribution': 2.0,
            'target_distribution': 2.0,
            'entry_steps': 1.5
        }
        
        total_improvement = 0
        for param, value in recommendations.items():
            factor = improvement_factors.get(param, 1.0)
            total_improvement += factor
        
        return min(total_improvement, 20.0)  # Cap at 20% estimated improvement
    
    def _estimate_settings_improvement(self, recommendations: Dict) -> float:
        """Estimate improvement from settings optimization."""
        return min(len(recommendations) * 2.5, 15.0)  # Simple estimation
    
    def _create_fallback_recommendations(self, optimization_type: str) -> Dict:
        """Create fallback recommendations if AI parsing fails."""
        if optimization_type == 'parameters':
            return {
                'risk_percentage': 1.5,
                'entry_steps': 2,
                'default_leverage': 3
            }
        elif optimization_type == 'strategy':
            return {
                'target_distribution': [60, 25, 15],
                'entry_distribution': [50, 30, 20]
            }
        else:
            return {
                'auto_stop_loss': True,
                'trailing_stop': True
            }