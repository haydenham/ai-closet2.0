# Outfit Recommendation Interface - Simplified Spec

## 📋 Overview
Simplify the outfit recommendation interface to a single text input where users describe the occasion and desired outfit. The system will automatically inject gender, style preferences, and weather data into the AI prompt.

---

## 🎯 Current State vs. Desired State

### Current Interface (Complex - 4 inputs):
```
1. Occasion (text input) - "What's the occasion?"
2. User Request (textarea) - "Describe what you want to wear"
3. Weather (dropdown) - "Hot/Warm/Mild/Cold"
4. Color Preference (optional text) - "Color preferences"
```

### New Interface (Simple - 1 input):
```
1. Single Prompt (textarea) - "Describe the occasion and what you want to wear"
```

---

## 🏗️ System Architecture

### Frontend (User-Facing)
```tsx
┌─────────────────────────────────────────────────────┐
│  Outfit Recommendation Page                         │
│                                                     │
│  ┌───────────────────────────────────────────────┐ │
│  │ Tell me about your occasion and what you'd    │ │
│  │ like to wear:                                 │ │
│  │                                               │ │
│  │ ┌───────────────────────────────────────────┐ │ │
│  │ │ e.g., "I have a casual brunch with        │ │ │
│  │ │ friends tomorrow and want something       │ │ │
│  │ │ comfortable but stylish"                  │ │ │
│  │ │                                           │ │ │
│  │ └───────────────────────────────────────────┘ │ │
│  │                                               │ │
│  │           [Generate Outfit] 🎨                │ │
│  └───────────────────────────────────────────────┘ │
│                                                     │
│  Auto-injected (shown as chips/tags):              │
│  • Your Style: Bohemian                            │
│  • Gender: Female                                  │
│  • Weather: Warm (72°F) ☀️                         │
└─────────────────────────────────────────────────────┘
```

### Backend (Data Processing)
```python
User Input: "Casual brunch with friends, something comfortable"

↓ System enriches with auto-data

Final Prompt to AI:
{
  "user_prompt": "Casual brunch with friends, something comfortable",
  "gender": "female",              # From user profile
  "style_category": "Bohemian",    # From quiz results
  "weather": "warm",               # From API or hardcoded
  "temperature": 72                # From API or hardcoded
}

↓ Gemini AI generates recommendation

Output: Outfit recommendation matched to user's closet
```

---

## 📊 Data Flow

### 1. **User Profile Data (Already Available)**
```typescript
// Fetched on page load
const userProfile = {
  gender: "female",           // From user.gender
  quiz_style: "Bohemian",     // From quiz_responses.primary_style
  secondary_style: "Classic"  // From quiz_responses.secondary_style
}
```

### 2. **Weather Data (Hardcoded → API Later)**
```typescript
// Phase 1: Hardcoded default
const weather = {
  condition: "warm",
  temperature: 72,
  emoji: "☀️"
}

// Phase 2: Integrate weather API (future)
const weather = await getWeatherForUser(userLocation)
```

### 3. **User Input (Single Field)**
```typescript
const userPrompt = "Casual brunch with friends, something comfortable but stylish"
```

### 4. **Combined Prompt to Backend**
```typescript
POST /outfit-recommendations/generate
{
  "prompt": "Casual brunch with friends, something comfortable but stylish"
  // System adds: gender, style, weather automatically
}
```

---

## 🔧 Technical Implementation

### Phase 1: Frontend Changes

#### **File: `GenerateRecommendations.tsx` (Simplified)**
```tsx
interface GenerateRecommendationsProps {
  onGenerate: (prompt: string) => Promise<void>
  loading?: boolean
  error?: string | null
  userStyle?: string | null
  userGender?: string | null
}

export const GenerateRecommendations: React.FC<GenerateRecommendationsProps> = ({
  onGenerate,
  loading,
  error,
  userStyle,
  userGender
}) => {
  const [prompt, setPrompt] = useState('')
  
  // Hardcoded weather for now
  const weather = {
    condition: 'warm',
    temperature: 72,
    emoji: '☀️'
  }

  return (
    <div className="space-y-4">
      {/* Auto-injected data display */}
      <div className="flex flex-wrap gap-2">
        {userStyle && (
          <Badge>Your Style: {userStyle}</Badge>
        )}
        {userGender && (
          <Badge>Gender: {userGender}</Badge>
        )}
        <Badge>Weather: {weather.condition} ({weather.temperature}°F) {weather.emoji}</Badge>
      </div>

      {/* Single prompt input */}
      <div>
        <label>Tell me about your occasion and what you'd like to wear</label>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="e.g., I have a work meeting and want something professional but comfortable..."
          rows={4}
        />
      </div>

      <Button onClick={() => onGenerate(prompt)} disabled={!prompt || loading}>
        {loading ? 'Generating...' : 'Generate Outfit 🎨'}
      </Button>
    </div>
  )
}
```

#### **File: `RecommendationsPage.tsx` (Updated)**
```tsx
const handleGenerate = async (prompt: string) => {
  setGenerating(true)
  
  try {
    // Backend automatically injects gender, style, weather
    const response = await api.post('/outfit-recommendations/generate', {
      prompt: prompt
    })
    
    await refetch()
  } catch (err) {
    setError(err.message)
  } finally {
    setGenerating(false)
  }
}

// Fetch user profile data on mount
useEffect(() => {
  const fetchUserData = async () => {
    const [profile, quiz] = await Promise.all([
      api.get('/users/me'),
      api.get('/quiz/responses/latest')
    ])
    
    setUserGender(profile.data.gender)
    setUserStyle(quiz.data.primary_style)
  }
  fetchUserData()
}, [])
```

---

### Phase 2: Backend Changes

#### **File: `outfit_recommendations.py` (Updated Endpoint)**

**Current:**
```python
@router.post("/generate")
async def generate_outfit_recommendation(
    request: SecureOutfitRequest,  # Has occasion, user_request, color, weather
    ...
):
    # Uses all 4 fields from request
```

**New:**
```python
class SimpleOutfitRequest(BaseModel):
    """Simplified outfit request - just user's prompt"""
    prompt: str = Field(..., min_length=10, max_length=1000)

@router.post("/generate")
async def generate_outfit_recommendation(
    request: SimpleOutfitRequest,
    db: Session = Depends(get_sync_session),
    current_user: User = Depends(get_current_user)
):
    """
    Generate outfit with auto-injected gender, style, weather data.
    User only provides a natural language prompt.
    """
    
    # 1. Get user's gender
    gender = current_user.gender  # From users table
    
    # 2. Get user's style from quiz
    quiz_result = ResponseService.get_user_latest_response(db, current_user.id)
    if not quiz_result:
        raise HTTPException(400, "Please complete the style quiz first")
    
    style_category = quiz_result.primary_style
    secondary_style = quiz_result.secondary_style
    
    # 3. Get/hardcode weather
    weather = "warm"  # Hardcoded for now
    temperature = 72   # Hardcoded for now
    
    # 4. Build enriched prompt for Gemini
    enriched_context = {
        "user_prompt": request.prompt,
        "gender": gender,
        "primary_style": style_category,
        "secondary_style": secondary_style,
        "weather": weather,
        "temperature": temperature
    }
    
    # 5. Generate with Gemini
    recommendation = await gemini_service.generate_outfit_recommendation_v2(
        enriched_context
    )
    
    return recommendation
```

#### **File: `gemini_service.py` (New Method)**
```python
async def generate_outfit_recommendation_v2(
    self,
    context: Dict[str, Any]
) -> OutfitRecommendation:
    """
    Generate outfit with enriched context.
    
    Args:
        context: {
            "user_prompt": "Casual brunch...",
            "gender": "female",
            "primary_style": "Bohemian",
            "secondary_style": "Classic",
            "weather": "warm",
            "temperature": 72
        }
    """
    
    # Build system prompt with context
    system_prompt = f"""You are a fashion stylist assistant.

USER PROFILE:
- Gender: {context['gender']}
- Primary Style: {context['primary_style']}
- Secondary Style: {context.get('secondary_style', 'N/A')}

ENVIRONMENT:
- Weather: {context['weather']} ({context['temperature']}°F)

USER REQUEST:
{context['user_prompt']}

Generate an outfit recommendation that:
1. Matches their style preferences ({context['primary_style']})
2. Is appropriate for {context['weather']} weather
3. Addresses their specific request

Return JSON with: top, bottom, shoes, accessories, reasoning.
"""
    
    # Call Gemini API
    response = await self._call_gemini_api(system_prompt)
    
    return self._parse_recommendation(response)
```

---

## 🎨 UI/UX Improvements

### Visual Design
```
┌─────────────────────────────────────────────────────────┐
│  Get Your Perfect Outfit                                │
│                                                         │
│  ┌─ Your Profile ────────────────────────────────────┐ │
│  │  👗 Bohemian Style  •  👤 Female  •  ☀️ Warm 72°F │ │
│  └──────────────────────────────────────────────────── │
│                                                         │
│  Describe your occasion and desired outfit:             │
│  ┌─────────────────────────────────────────────────┐  │
│  │                                                 │  │
│  │  [Textarea with placeholder examples]          │  │
│  │                                                 │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  Examples:                                              │
│  • "Casual brunch with friends, comfortable but chic"  │
│  • "Job interview, need to look professional"          │
│  • "Weekend errands, something practical"              │
│                                                         │
│              [Generate Outfit 🎨]                       │
└─────────────────────────────────────────────────────────┘
```

### Interaction States

**Empty State:**
```
💬 Tell me what you're planning...
```

**Typing State:**
```
"I have a casual brunch with friends tomorrow..."
✓ Valid prompt (50 characters)
```

**Loading State:**
```
🤖 Nomi is designing your perfect outfit...
✓ Using your Bohemian style preferences
✓ Matched to warm weather (72°F)
```

**Success State:**
```
✨ Your outfit is ready!
[Show outfit recommendation]
```

---

## 📈 Benefits of This Approach

### For Users:
✅ **Simpler**: One text box instead of 4 fields  
✅ **More Natural**: Describe in their own words  
✅ **Faster**: Less clicking/selecting  
✅ **Smarter**: System knows their preferences  

### For System:
✅ **Better Context**: Quiz data + user prompt combined  
✅ **Consistency**: Style always matches quiz results  
✅ **Maintainable**: Fewer form fields to validate  
✅ **Extensible**: Easy to add weather API later  

---

## 🚀 Implementation Plan

### **Phase 1: Core Simplification** (This PR)
- [ ] Update `GenerateRecommendations.tsx` to single prompt input
- [ ] Show auto-injected data as read-only badges
- [ ] Update backend endpoint to accept simple prompt
- [ ] Fetch user gender and quiz style on page load
- [ ] Hardcode weather to "warm" / 72°F
- [ ] Update Gemini prompt building logic

### **Phase 2: Polish** (Next PR)
- [ ] Add example prompts for inspiration
- [ ] Add character counter (min 10, max 1000)
- [ ] Add loading states with context ("Using your Bohemian style...")
- [ ] Improve error messaging
- [ ] Add prompt suggestions based on time of day

### **Phase 3: Weather Integration** (Future)
- [ ] Integrate weather API (OpenWeatherMap / WeatherAPI)
- [ ] Use user's location or allow manual location input
- [ ] Auto-update weather data every hour
- [ ] Show weather forecast for the week

---

## 🧪 Testing Checklist

### Frontend Tests:
- [ ] Prompt input accepts text
- [ ] Auto-injected data displays correctly (style, gender, weather)
- [ ] Empty prompt shows validation error
- [ ] Long prompt (>1000 chars) shows validation error
- [ ] Loading state displays during generation
- [ ] Success state shows recommendation
- [ ] Error state shows helpful message

### Backend Tests:
- [ ] Endpoint rejects requests without quiz completion
- [ ] Gender and style correctly pulled from database
- [ ] Prompt is properly enriched with context
- [ ] Gemini receives well-formatted prompt
- [ ] Recommendation saves with correct metadata

### Integration Tests:
- [ ] End-to-end: User types prompt → Gets outfit
- [ ] Quiz results correctly influence recommendations
- [ ] Weather data (hardcoded) is included in prompt
- [ ] Generated outfits match user's style profile

---

## 📝 API Contract

### Request
```typescript
POST /outfit-recommendations/generate

{
  "prompt": "Casual brunch with friends, something comfortable but stylish"
}
```

### Response
```typescript
{
  "success": true,
  "recommendation": {
    "id": "uuid",
    "outfit_items": [...],
    "reasoning": "...",
    "style_match_score": 0.92
  },
  "context_used": {
    "gender": "female",
    "style": "Bohemian",
    "weather": "warm"
  }
}
```

---

## 🎯 Success Metrics

- **User Engagement**: Increase in recommendation generations (simpler = more usage)
- **Completion Rate**: % of users who complete the prompt (target: >80%)
- **Satisfaction**: User ratings on recommendations (target: >4/5)
- **Error Rate**: Validation errors (target: <5%)

---

## 💬 Example Prompts

**Good Examples:**
- ✅ "I have a casual brunch with friends tomorrow and want something comfortable but stylish"
- ✅ "Need an outfit for a job interview - professional but not too formal"
- ✅ "Going to a concert tonight, want something fun and easy to move in"
- ✅ "Weekend errands - need something practical but put-together"

**Bad Examples (Too Vague):**
- ❌ "Something nice" (missing occasion)
- ❌ "Outfit" (no context)
- ❌ "Clothes" (too generic)

---

## 🔮 Future Enhancements

1. **Smart Suggestions**: 
   - "Based on your calendar, you have a meeting at 2pm. Generate outfit?"
   
2. **Seasonal Intelligence**:
   - "It's Monday morning in fall - coffee shop work outfit?"

3. **Context Memory**:
   - "Similar to what you wore to brunch last week, but more casual"

4. **Multi-day Planning**:
   - "Generate outfits for my 3-day work trip to Seattle"

---

## ✅ Definition of Done

- [ ] User can input single prompt describing occasion + outfit desires
- [ ] System auto-injects gender from user profile
- [ ] System auto-injects style from quiz results
- [ ] System auto-injects hardcoded weather (warm, 72°F)
- [ ] Backend builds enriched prompt for Gemini
- [ ] Frontend displays auto-injected data as badges
- [ ] Old 4-field form is removed
- [ ] All existing tests pass
- [ ] New tests cover simplified flow
- [ ] Documentation updated

---

**Ready to implement! 🚀**
