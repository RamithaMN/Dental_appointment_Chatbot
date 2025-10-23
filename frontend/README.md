# Dental Chatbot Frontend

A modern, responsive React/Next.js frontend for the Dental Chatbot API with real-time chat interface and appointment booking functionality.

## 🚀 Features

- **🔐 Secure Authentication** - JWT-based token authentication
- **💬 Real-time Chat Interface** - Interactive chatbot with typing indicators
- **📅 Appointment Booking** - Complete appointment scheduling system
- **📱 Responsive Design** - Mobile-first, works on all devices
- **🎨 Modern UI/UX** - Clean, intuitive interface with Tailwind CSS
- **⚡ Fast Performance** - Optimized with Next.js 14
- **🔒 Type Safety** - Full TypeScript support

## 🛠️ Technology Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **HTTP Client**: Axios
- **State Management**: React Context API

## 📦 Installation

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Backend API running on http://localhost:8000

### Setup

1. **Clone and install dependencies:**
```bash
cd /Users/rohitsundaram/PycharmProjects/dental-chatbot-frontend
npm install
```

2. **Configure environment:**
```bash
# Create .env.local file
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
```

3. **Start development server:**
```bash
npm run dev
```

4. **Open in browser:**
```
http://localhost:3000
```

## 🎯 Usage

### 1. Authentication

1. Open http://localhost:3000
2. Enter API key: `dental-chatbot-api-key-2025`
3. Click "Sign In"

### 2. Chat Interface

- **Send Messages**: Type in the input field and press Enter
- **Quick Messages**: Click on suggested questions
- **Clear Chat**: Use the trash icon to clear conversation
- **Sign Out**: Use the logout icon

### 3. Appointment Booking

- Click on appointment-related messages
- Fill out the appointment form
- Submit your request

## 🏗️ Project Structure

```
src/
├── app/                    # Next.js App Router
│   ├── layout.tsx         # Root layout with providers
│   ├── page.tsx           # Main page component
│   └── globals.css         # Global styles
├── components/             # React components
│   ├── LoginForm.tsx       # Authentication form
│   ├── ChatInterface.tsx  # Main chat interface
│   ├── MessageBubble.tsx  # Individual message component
│   └── AppointmentForm.tsx # Appointment booking form
├── contexts/              # React Context providers
│   └── AuthContext.tsx    # Authentication context
├── hooks/                 # Custom React hooks
│   └── useChat.ts         # Chat functionality hook
└── lib/                   # Utility libraries
    └── api.ts             # API client configuration
```

## 🔧 Configuration

### Environment Variables

Create `.env.local`:

```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# Optional: Custom API key for demo
NEXT_PUBLIC_DEMO_API_KEY=dental-chatbot-api-key-2025
```

### API Integration

The frontend connects to the FastAPI backend with these endpoints:

- `POST /api/chatbot/token` - Generate JWT token
- `GET /api/chatbot/verify` - Verify token
- `POST /api/chatbot/chat` - Send chat message

## 🎨 Customization

### Styling

The app uses Tailwind CSS with custom components:

```css
/* Custom components in globals.css */
.btn-primary { /* Primary button styles */ }
.message-bubble { /* Chat message styles */ }
.card { /* Card container styles */ }
```

### Themes

The app supports light/dark mode (future feature):

```css
@media (prefers-color-scheme: dark) {
  .dark-mode { /* Dark theme styles */ }
}
```

## 📱 Responsive Design

- **Mobile**: Optimized for phones (320px+)
- **Tablet**: Enhanced for tablets (768px+)
- **Desktop**: Full experience (1024px+)

## 🔒 Security Features

- **JWT Tokens**: Secure authentication
- **Token Storage**: LocalStorage
- **CORS Protection**: Configured for backend
- **Input Validation**: Client-side validation
- **XSS Protection**: Sanitized inputs

## 🚀 Deployment

### Production Build

```bash
npm run build
npm start
```

### Docker Deployment

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

### Environment Variables for Production

```env
NEXT_PUBLIC_API_URL=https://your-api-domain.com
```

## 🧪 Testing

### Manual Testing

1. **Authentication Flow:**
   - Test with valid API key
   - Test with invalid API key
   - Test token persistence

2. **Chat Interface:**
   - Send various message types
   - Test quick message buttons
   - Test message history

3. **Appointment Booking:**
   - Fill out appointment form
   - Test form validation
   - Test form submission

### API Testing

```bash
# Test backend connection
curl http://localhost:8000/health

# Test token generation
curl -X POST http://localhost:8000/api/chatbot/token \
  -H "Content-Type: application/json" \
  -d '{"api_key": "dental-chatbot-api-key-2025"}'
```

## 🐛 Troubleshooting

### Common Issues

1. **CORS Errors:**
   - Ensure backend CORS is configured for frontend URL
   - Check API_URL environment variable

2. **Authentication Issues:**
   - Verify API key is correct
   - Check token expiration
   - Clear localStorage if needed

3. **Styling Issues:**
   - Ensure Tailwind CSS is properly configured
   - Check for CSS conflicts

### Debug Mode

Enable debug logging:

```javascript
// In browser console
localStorage.setItem('debug', 'true');
```

## 📈 Performance

### Optimization Features

- **Code Splitting**: Automatic with Next.js
- **Image Optimization**: Next.js Image component
- **Bundle Analysis**: `npm run build` shows bundle size
- **Lazy Loading**: Components loaded on demand

### Performance Monitoring

```bash
# Analyze bundle
npm run build
npm run analyze
```

## 🔄 Updates

### Version Updates

```bash
# Update dependencies
npm update

# Check for security vulnerabilities
npm audit
```

## 📞 Support

### Getting Help

1. **Documentation**: Check this README
2. **API Docs**: http://localhost:8000/docs
3. **Issues**: Check browser console for errors

### Development

```bash
# Start development with hot reload
npm run dev

# Run linting
npm run lint

# Type checking
npx tsc --noEmit
```

## 📄 License

MIT License - See LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

**Built with ❤️ using Next.js, TypeScript, and Tailwind CSS**