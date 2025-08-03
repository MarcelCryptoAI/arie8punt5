# Bitunix Signal Trading Bot

Een volledig geautomatiseerde cryptocurrency trading bot met Telegram signal parsing, AI optimalisatie, en uitgebreide backtesting functionaliteit.

## 🚀 Features

- **Telegram Signal Parsing**: Automatische parsing van trading signalen met robuuste tekst-analyse
- **Live Trading**: Directe integratie met Bitunix API voor real-time trading
- **AI Optimalisatie**: Machine learning voor parameter tuning en strategie verbetering
- **Backtesting**: Uitgebreide backtesting met historische data simulatie
- **Modern Dashboard**: Real-time monitoring en beheer via web interface
- **Risk Management**: Geavanceerde risicobeheer tools en instellingen
- **Multi-vendor Support**: Uitbreidbaar design voor meerdere exchanges

## 🛠️ Tech Stack

### Backend
- **Flask** - Python web framework
- **SQLAlchemy** - Database ORM
- **OpenAI/Anthropic** - AI integratie
- **Requests** - API communicatie
- **Pandas/NumPy** - Data analyse

### Frontend
- **React** - UI framework
- **Tailwind CSS** - Styling
- **Recharts** - Data visualisatie
- **Axios** - API calls
- **React Router** - Navigatie

### Deployment
- **Heroku** - Cloud hosting
- **PostgreSQL** - Production database
- **Gunicorn** - WSGI server

## 📋 Installatie

### Lokale Development

1. **Clone Repository**
```bash
git clone https://github.com/MarcelCryptoAI/arietelegramn.git
cd arietelegramn
```

2. **Backend Setup**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# of: venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

3. **Environment Variables**
```bash
cp .env.example .env
# Bewerk .env bestand met je API keys
```

4. **Database Initialisatie**
```bash
flask db init
flask db migrate
flask db upgrade
```

5. **Frontend Setup**
```bash
cd ../frontend
npm install
```

6. **Start Development Servers**

Terminal 1 (Backend):
```bash
cd backend
source venv/bin/activate
python app.py
```

Terminal 2 (Frontend):
```bash
cd frontend
npm start
```

### Heroku Deployment

1. **Heroku CLI Setup**
```bash
heroku login
heroku create your-app-name
```

2. **Environment Variables**
```bash
heroku config:set SECRET_KEY=your-secret-key
heroku config:set OPENAI_API_KEY=your-openai-key
heroku config:set ANTHROPIC_API_KEY=your-anthropic-key
heroku config:set ENCRYPTION_KEY=your-encryption-key
```

3. **Deploy**
```bash
git add .
git commit -m "Initial deployment"
git push heroku main
```

4. **Database Setup**
```bash
heroku run python backend/app.py db upgrade
```

## ⚙️ Configuratie

### 1. Bitunix API Setup
1. Ga naar Bitunix exchange
2. Maak API keys aan met trading permissions
3. Vul API credentials in via Settings pagina
4. Test de verbinding

### 2. AI Configuration
1. Verkrijg OpenAI of Anthropic API key
2. Configureer via environment variables
3. Enable AI features in Settings

### 3. Trading Parameters
- **Leverage**: 1-100x (standaard: 5x)
- **Risk Percentage**: 0.1-10% (standaard: 2%)
- **Entry Steps**: 1-5 (standaard: 3)
- **Position Size**: Minimaal $10 USDT

## 📊 Gebruik

### Signal Parsing
1. Ga naar **Signals** pagina
2. Klik **Add Signal** of **Batch Import**
3. Plak Telegram signal tekst
4. Automatische parsing en validatie
5. Bekijk parsed resultaten

### Live Trading
1. Configureer API keys in **Settings**
2. Parsed signals verschijnen in signals lijst
3. Klik **Execute** om trade te starten
4. Monitor trades in **Trades** sectie

### Backtesting
1. Ga naar **Backtest** pagina
2. Maak nieuwe backtest aan
3. Voeg signals toe (historisch of template)
4. Run backtest en analyseer resultaten

### AI Optimalisatie
1. Enable AI in **Settings**
2. Ga naar **AI Optimization**
3. Run analysis voor aanbevelingen
4. Apply optimalisaties automatisch

## 🔧 API Endpoints

### Signals
- `GET /api/signals` - Alle signals
- `POST /api/signals/parse` - Parse single signal
- `POST /api/signals/batch-parse` - Batch parsing
- `PUT /api/signals/{id}` - Update signal
- `DELETE /api/signals/{id}` - Delete signal

### Trades
- `GET /api/trades` - Alle trades
- `POST /api/trades/execute/{signal_id}` - Execute signal
- `POST /api/trades/{id}/close` - Close trade
- `GET /api/trades/active` - Active trades
- `GET /api/trades/stats` - Trading statistics

### Settings
- `GET /api/settings` - Current settings
- `PUT /api/settings` - Update settings
- `POST /api/settings/test-connection` - Test API

### Backtest
- `GET /api/backtest` - All backtests
- `POST /api/backtest/create` - Create backtest
- `POST /api/backtest/{id}/run` - Run backtest

### AI
- `POST /api/ai/optimize-settings` - AI optimization
- `GET /api/ai/suggestions` - Get AI suggestions
- `POST /api/ai/optimizations/{id}/apply` - Apply optimization

## 🔐 Security

- API keys encrypted in database
- HTTPS enforced in production
- Input validation en sanitization
- Rate limiting op API endpoints
- Secure environment variable handling

## 📈 Signal Format Support

De bot ondersteunt diverse Telegram signal formaten:

```
#BTC/USDT
LONG
Entry: 45000-46000
Leverage: 5x
Targets: 47000, 48000, 49000
Stop Loss: 44000
```

```
$ETH SHORT
Entry Zone: 3200-3250
Cross Leverage 3x
TP: 3100, 3000, 2900
SL: 3300
```

## 🚨 Risk Disclaimer

**WAARSCHUWING**: Cryptocurrency trading brengt significante financiële risico's met zich mee. Deze bot is een tool en geen financieel advies. Gebruik alleen geld dat je kunt verliezen.

- Test altijd eerst op testnet
- Start met kleine posities
- Monitor performance regelmatig
- Gebruik adequate risk management

## 🤝 Contributing

1. Fork het project
2. Maak feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push naar branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📝 License

Distributed under the MIT License. See `LICENSE` for more information.

## 🔗 Links

- **Live Demo**: https://arietelegram-1d3bfa587442.herokuapp.com/
- **Repository**: https://github.com/MarcelCryptoAI/arietelegramn.git
- **Issues**: https://github.com/MarcelCryptoAI/arietelegramn/issues

## 📞 Support

Voor support en vragen:
- Open een GitHub Issue
- Contact via repository

---

**Gemaakt met ❤️ voor de crypto trading community**