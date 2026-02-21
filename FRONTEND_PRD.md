# CardioTwin Frontend PRD
## 3D Digital Twin Health Visualization Platform

**Version:** 1.0  
**Date:** February 21, 2026  
**Backend URL:** https://cardiotwin-jqrct.ondigitalocean.app  
**API Docs:** https://cardiotwin-jqrct.ondigitalocean.app/docs

---

## 1. Executive Summary

CardioTwin is a real-time cardiac health monitoring platform that creates a **3D digital twin avatar** visualizing the user's biometric state. The avatar dynamically changes colors, animations, and visual effects based on live health data, creating an intuitive and engaging way to understand cardiac wellness.

### Core Experience
- **Real-time biometric visualization** on a 3D human avatar
- **Zone-based color system** (Green → Yellow → Orange → Red) reflecting health state
- **Particle effects and animations** showing stress levels and vitals
- **"What-If" projection mode** visualizing future health trajectories
- **AI-powered nudges** displayed as contextual notifications

---

## 2. User Personas

### Primary: Health-Conscious Individual
- Wants to understand their cardiac health in real-time
- Prefers visual feedback over numbers
- Uses the app during workouts, meditation, or daily monitoring

### Secondary: Caregiver/Family Member
- Monitors a loved one's health remotely
- Needs clear visual indicators of health state
- Receives alerts when intervention may be needed

---

## 3. Technical Stack (Recommended)

| Layer | Technology | Purpose |
|-------|------------|---------|
| Framework | Next.js 14+ / React 18+ | App foundation |
| 3D Engine | Three.js + React Three Fiber | 3D avatar rendering |
| 3D Models | Ready Player Me / Mixamo | Avatar generation |
| Animation | GSAP / Framer Motion | Smooth transitions |
| Charts | Recharts / Chart.js | Score history visualization |
| State | Zustand / React Query | State management |
| Styling | Tailwind CSS | Responsive design |
| Icons | Lucide React | UI icons |

---

## 4. Core Features

### 4.1 Session Management

#### 4.1.1 Session Start Screen
```
┌─────────────────────────────────────────┐
│                                         │
│         🫀 CardioTwin                   │
│                                         │
│    ┌─────────────────────────────┐      │
│    │  Your Digital Health Twin   │      │
│    └─────────────────────────────┘      │
│                                         │
│         [ Start Session ]               │
│                                         │
│    "Connect your sensors to begin"      │
│                                         │
└─────────────────────────────────────────┘
```

**API Call:**
```javascript
POST /api/session/start
Body: { session_id: "session-{timestamp}", user_id: "user-123" }
```

---

### 4.2 Calibration Phase (Readings 1-15)

#### 4.2.1 Calibration UI Requirements

The system needs **15 readings** to establish the user's personal baseline. During calibration, show:

```
┌─────────────────────────────────────────┐
│                                         │
│         🔄 Calibrating...               │
│                                         │
│    ████████████░░░░░░░░░  8/15          │
│                                         │
│    "Learning your unique baseline"      │
│                                         │
│    ┌─────────────────────────────┐      │
│    │                             │      │
│    │     [3D Avatar - Neutral]   │      │
│    │     Subtle breathing anim   │      │
│    │     Soft white/blue glow    │      │
│    │                             │      │
│    └─────────────────────────────┘      │
│                                         │
│    Live readings streaming...           │
│    ❤️ 72 bpm  📊 45ms  🫁 98%  🌡️ 36.6°│
│                                         │
└─────────────────────────────────────────┘
```

#### 4.2.2 Calibration Avatar State
- **Color:** Neutral white/silver with subtle blue ambient glow
- **Animation:** Gentle breathing animation (chest expansion)
- **Particles:** Soft, slow-moving particles around the heart area
- **Opacity:** Slightly translucent (0.8) until calibration complete

#### 4.2.3 API Response Handling
```javascript
// Response when calibrating
{
  "status": "calibrating",
  "readings_collected": 8,
  "readings_needed": 15,
  "alert": false
}

// Update progress bar
const progress = readings_collected / readings_needed; // 0.53
```

---

### 4.3 Live Monitoring Dashboard (Post-Calibration)

#### 4.3.1 Main Dashboard Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  CardioTwin                              🔔  ⚙️  👤             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────┐  ┌───────────────────────────────┐│
│  │                         │  │                               ││
│  │                         │  │    CardioTwin Score           ││
│  │    [3D AVATAR]          │  │                               ││
│  │                         │  │         74.2                  ││
│  │    Zone colors applied  │  │        🟡 Mild Strain         ││
│  │    Heart glow effect    │  │                               ││
│  │    Particle system      │  │    ┌─────────────────────┐    ││
│  │                         │  │    │ ▁▂▃▅▆▇█▇▆▅▃▂▁▂▃▅▆ │    ││
│  │                         │  │    │    Score History    │    ││
│  │                         │  │    └─────────────────────┘    ││
│  │                         │  │                               ││
│  └─────────────────────────┘  └───────────────────────────────┘│
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  Component Breakdown                                        ││
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                       ││
│  │  │ HRV  │ │  HR  │ │ SpO2 │ │ Temp │                       ││
│  │  │ 65.6 │ │ 58.5 │ │ 95.0 │ │ 96.0 │                       ││
│  │  │ 40%  │ │ 25%  │ │ 20%  │ │ 15%  │                       ││
│  │  └──────┘ └──────┘ └──────┘ └──────┘                       ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  💡 AI Nudge: "Consider taking a short break and some      ││
│  │     deep breaths. Your HRV indicates mild stress." 💛       ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 4.3.2 API Response (Scored Reading)
```javascript
{
  "status": "scored",
  "score": 74.2,
  "zone": "YELLOW",
  "zone_label": "Mild Strain",
  "zone_emoji": "🟡",
  "alert": false,
  "nudge_sent": false,
  "components": {
    "heart_rate": { "value": 85.0, "score": 58.5 },
    "hrv": { "value": 35.0, "score": 65.6 },
    "spo2": { "value": 96.0, "score": 95.0 },
    "temperature": { "value": 37.0, "score": 96.0 }
  },
  "baseline": {
    "resting_bpm": 72.0,
    "resting_hrv": 45.0,
    "normal_spo2": 98.0,
    "normal_temp": 36.6
  }
}
```

---

## 5. 3D Digital Twin Avatar System

### 5.1 Avatar Requirements

#### 5.1.1 Base Model
- **Format:** GLB/GLTF (optimized for web)
- **Polygon Count:** 10K-30K (performance optimized)
- **Rigging:** Full body rig with blend shapes for expressions
- **Texture:** PBR materials with emissive channels for glow effects
- **Recommended Sources:**
  - Ready Player Me (custom avatars)
  - Mixamo (free rigged models)
  - Sketchfab (premium models)

#### 5.1.2 Key Body Regions for Visualization

| Region | Data Mapped | Visual Effect |
|--------|-------------|---------------|
| **Heart/Chest** | Overall Score | Pulsing glow, particle emission |
| **Full Body** | Zone Status | Color tint overlay |
| **Head/Face** | Stress Level | Expression blend shapes |
| **Skin Surface** | Temperature | Heat map gradient |
| **Circulatory** | HR/HRV | Flowing particle streams |

### 5.2 Zone-Based Color System

#### 5.2.1 Color Definitions

```javascript
const ZONE_COLORS = {
  GREEN: {
    primary: '#22c55e',      // Main zone color
    glow: '#4ade80',         // Emissive glow
    particle: '#86efac',     // Particle color
    ambient: '#dcfce7',      // Background ambient
    intensity: 0.3,          // Glow intensity
    label: 'Thriving'
  },
  YELLOW: {
    primary: '#eab308',
    glow: '#facc15',
    particle: '#fde047',
    ambient: '#fef9c3',
    intensity: 0.5,
    label: 'Mild Strain'
  },
  ORANGE: {
    primary: '#f97316',
    glow: '#fb923c',
    particle: '#fdba74',
    ambient: '#ffedd5',
    intensity: 0.7,
    label: 'Moderate Strain'
  },
  RED: {
    primary: '#ef4444',
    glow: '#f87171',
    particle: '#fca5a5',
    ambient: '#fee2e2',
    intensity: 1.0,
    label: 'High Strain'
  }
};
```

#### 5.2.2 Score to Zone Mapping

```javascript
function getZoneFromScore(score) {
  if (score >= 80) return 'GREEN';
  if (score >= 55) return 'YELLOW';
  if (score >= 30) return 'ORANGE';
  return 'RED';
}
```

### 5.3 Visual Effects Specifications

#### 5.3.1 Heart Glow Effect

The heart area should have a pulsating glow that reflects the current zone and heart rate.

```javascript
// Heart Glow Parameters
const heartGlowConfig = {
  // Pulse frequency matches actual BPM
  pulseFrequency: bpm / 60, // Hz (e.g., 72 bpm = 1.2 Hz)
  
  // Glow intensity based on zone
  baseIntensity: ZONE_COLORS[zone].intensity,
  
  // Pulse amplitude (how much it varies)
  pulseAmplitude: 0.3,
  
  // Glow color from zone
  color: ZONE_COLORS[zone].glow,
  
  // Glow radius
  radius: 0.15, // meters from heart center
};

// Animation function
function animateHeartGlow(time) {
  const pulse = Math.sin(time * heartGlowConfig.pulseFrequency * Math.PI * 2);
  const intensity = heartGlowConfig.baseIntensity + 
                    (pulse * heartGlowConfig.pulseAmplitude);
  return intensity;
}
```

**React Three Fiber Implementation:**
```jsx
import { useFrame } from '@react-three/fiber';
import { useRef } from 'react';

function HeartGlow({ bpm, zone }) {
  const glowRef = useRef();
  
  useFrame(({ clock }) => {
    const time = clock.getElapsedTime();
    const pulse = Math.sin(time * (bpm / 60) * Math.PI * 2);
    const intensity = ZONE_COLORS[zone].intensity + (pulse * 0.3);
    glowRef.current.material.emissiveIntensity = intensity;
  });
  
  return (
    <mesh ref={glowRef} position={[0, 1.3, 0.1]}>
      <sphereGeometry args={[0.15, 32, 32]} />
      <meshStandardMaterial
        color={ZONE_COLORS[zone].primary}
        emissive={ZONE_COLORS[zone].glow}
        emissiveIntensity={0.5}
        transparent
        opacity={0.6}
      />
    </mesh>
  );
}
```

#### 5.3.2 Particle System

Particles flow around the avatar representing circulatory health and energy.

```javascript
const particleConfig = {
  GREEN: {
    count: 100,
    speed: 0.5,           // Calm, slow movement
    size: 0.02,
    spread: 0.3,
    pattern: 'orbital',   // Gentle orbit around body
    lifespan: 3000,       // ms
  },
  YELLOW: {
    count: 150,
    speed: 0.8,
    size: 0.025,
    spread: 0.4,
    pattern: 'orbital',
    lifespan: 2500,
  },
  ORANGE: {
    count: 200,
    speed: 1.2,
    size: 0.03,
    spread: 0.5,
    pattern: 'chaotic',   // More erratic movement
    lifespan: 2000,
  },
  RED: {
    count: 300,
    speed: 2.0,           // Fast, urgent movement
    size: 0.035,
    spread: 0.6,
    pattern: 'chaotic',
    lifespan: 1500,
  }
};
```

**React Three Fiber Particles:**
```jsx
import { useFrame } from '@react-three/fiber';
import { useMemo, useRef } from 'react';
import * as THREE from 'three';

function HealthParticles({ zone, score }) {
  const config = particleConfig[zone];
  const particlesRef = useRef();
  
  const particles = useMemo(() => {
    const positions = new Float32Array(config.count * 3);
    for (let i = 0; i < config.count; i++) {
      positions[i * 3] = (Math.random() - 0.5) * config.spread;
      positions[i * 3 + 1] = Math.random() * 2; // Height
      positions[i * 3 + 2] = (Math.random() - 0.5) * config.spread;
    }
    return positions;
  }, [config.count, config.spread]);
  
  useFrame(({ clock }) => {
    const time = clock.getElapsedTime();
    const positions = particlesRef.current.geometry.attributes.position.array;
    
    for (let i = 0; i < config.count; i++) {
      const i3 = i * 3;
      // Animate based on pattern
      if (config.pattern === 'orbital') {
        positions[i3] += Math.sin(time + i) * 0.001 * config.speed;
        positions[i3 + 2] += Math.cos(time + i) * 0.001 * config.speed;
      } else {
        positions[i3] += (Math.random() - 0.5) * 0.01 * config.speed;
        positions[i3 + 1] += (Math.random() - 0.5) * 0.01 * config.speed;
        positions[i3 + 2] += (Math.random() - 0.5) * 0.01 * config.speed;
      }
    }
    particlesRef.current.geometry.attributes.position.needsUpdate = true;
  });
  
  return (
    <points ref={particlesRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={config.count}
          array={particles}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial
        size={config.size}
        color={ZONE_COLORS[zone].particle}
        transparent
        opacity={0.8}
        sizeAttenuation
      />
    </points>
  );
}
```

#### 5.3.3 Body Color Overlay

The avatar's skin/body should have a subtle color tint based on zone:

```javascript
// Shader-based color overlay
const bodyOverlayConfig = {
  GREEN: { tint: [0.13, 0.77, 0.37], opacity: 0.1 },   // Subtle green
  YELLOW: { tint: [0.92, 0.70, 0.03], opacity: 0.15 }, // Light yellow
  ORANGE: { tint: [0.98, 0.45, 0.09], opacity: 0.2 },  // Warm orange
  RED: { tint: [0.94, 0.27, 0.27], opacity: 0.25 },    // Alert red
};

// Apply as post-processing or material overlay
function applyZoneTint(material, zone) {
  const config = bodyOverlayConfig[zone];
  material.color.setRGB(...config.tint);
  material.opacity = 1 - config.opacity;
}
```

#### 5.3.4 Breathing Animation

The avatar should have a breathing animation that reflects stress level:

```javascript
const breathingConfig = {
  GREEN: {
    rate: 12,        // Breaths per minute (calm)
    depth: 0.02,     // Chest expansion amount
    rhythm: 'smooth' // Sine wave
  },
  YELLOW: {
    rate: 16,
    depth: 0.025,
    rhythm: 'smooth'
  },
  ORANGE: {
    rate: 20,
    depth: 0.03,
    rhythm: 'sharp'  // More abrupt transitions
  },
  RED: {
    rate: 25,        // Rapid breathing
    depth: 0.04,
    rhythm: 'sharp'
  }
};
```

### 5.4 Component Visualization on Avatar

Each health component should have a dedicated visualization region:

#### 5.4.1 Heart Rate (HR) - Chest Area
```javascript
// Pulsing ring around heart
const hrVisualization = {
  position: [0, 1.3, 0.1],  // Chest center
  type: 'pulse-ring',
  frequency: bpm / 60,
  color: getComponentColor(components.heart_rate.score),
  size: 0.2 + (0.1 * (1 - components.heart_rate.score / 100))
};
```

#### 5.4.2 HRV - Nervous System (Spine/Back Glow)
```javascript
// Flowing energy along spine
const hrvVisualization = {
  startPosition: [0, 0.5, -0.1],  // Lower back
  endPosition: [0, 1.8, -0.1],    // Upper back/neck
  type: 'energy-flow',
  flowSpeed: components.hrv.score / 50, // Slower = more relaxed
  color: getComponentColor(components.hrv.score),
  intensity: components.hrv.score / 100
};
```

#### 5.4.3 SpO2 - Lung Area (Both Sides of Chest)
```javascript
// Breathing spheres in lung positions
const spo2Visualization = {
  leftLung: [-0.15, 1.35, 0.05],
  rightLung: [0.15, 1.35, 0.05],
  type: 'breathing-sphere',
  opacity: components.spo2.score / 100,
  color: interpolateColor(
    '#fee2e2', // Low O2 - pale
    '#60a5fa', // High O2 - blue
    components.spo2.score / 100
  )
};
```

#### 5.4.4 Temperature - Full Body Heat Map
```javascript
// Heat map gradient shader
const tempVisualization = {
  type: 'heat-map',
  temperature: components.temperature.value,
  normalTemp: baseline.normal_temp,
  colorMap: {
    cold: '#3b82f6',    // Below normal - blue
    normal: '#22c55e',  // Normal - green
    warm: '#eab308',    // Slightly elevated - yellow
    hot: '#ef4444'      // High - red
  },
  deviation: Math.abs(components.temperature.value - baseline.normal_temp)
};
```

---

## 6. "What-If" Projection Mode

### 6.1 Projection Feature Overview

The projection mode shows the user what their health might look like in the future based on current trends.

```
┌─────────────────────────────────────────────────────────────────┐
│                     PROJECTION MODE                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│    ┌─────────────┐         ┌─────────────┐                     │
│    │   TODAY     │   →→→   │  IN 30 DAYS │                     │
│    │             │         │             │                     │
│    │  [Avatar]   │         │  [Avatar]   │                     │
│    │   🟡 74.2   │         │   🟠 60.6   │                     │
│    │             │         │             │                     │
│    └─────────────┘         └─────────────┘                     │
│                                                                 │
│    ┌─────────────────────────────────────────────────────────┐ │
│    │              Projection Timeline                         │ │
│    │                                                          │ │
│    │  100 ─┬─────────────────────────────────────            │ │
│    │       │ ████                                             │ │
│    │   74 ─┤      ████                                        │ │
│    │       │          ████                                    │ │
│    │   60 ─┤              ████████████████████                │ │
│    │       │                                                  │ │
│    │   30 ─┼─────────────────────────────────────            │ │
│    │       Today    10d     20d     30d                      │ │
│    └─────────────────────────────────────────────────────────┘ │
│                                                                 │
│    ⚠️  If current patterns continue:                           │
│        • Score may drop from 74.2 → 60.6                       │
│        • Resting HR may increase by +2 bpm                     │
│        • Risk category: Mild Strain → Moderate Strain          │
│                                                                 │
│    💡 Recommendation: Increase daily activity and              │
│       ensure 7-8 hours of quality sleep.                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 API Integration

```javascript
// Get projection
POST /api/predict
Body: { session_id: "session-123", days: 30 }

// Response
{
  "current_score": 74.2,
  "projected_score": 60.6,
  "projected_resting_hr_increase_bpm": 2.0,
  "current_risk_category": "Mild Strain",
  "projected_risk_category": "Moderate Strain",
  "disclaimer": "Statistical projection only. Not a medical diagnosis."
}
```

### 6.3 Dual Avatar Comparison View

Show two avatars side-by-side:

```jsx
function ProjectionView({ currentData, projectionData }) {
  return (
    <div className="flex gap-8 justify-center">
      {/* Current State Avatar */}
      <div className="text-center">
        <h3>Today</h3>
        <Canvas>
          <Avatar 
            zone={getZoneFromScore(currentData.current_score)}
            score={currentData.current_score}
            opacity={1}
          />
        </Canvas>
        <ScoreBadge score={currentData.current_score} />
      </div>
      
      {/* Animated Arrow */}
      <div className="flex items-center">
        <Arrow animated direction="right" />
        <span className="text-sm">In {projectionData.days} days</span>
      </div>
      
      {/* Projected State Avatar */}
      <div className="text-center">
        <h3>Projected</h3>
        <Canvas>
          <Avatar 
            zone={getZoneFromScore(projectionData.projected_score)}
            score={projectionData.projected_score}
            opacity={0.7}  // Slightly translucent to indicate projection
            isProjection={true}
          />
          {/* Ghost/hologram effect for projection */}
          <ProjectionOverlay />
        </Canvas>
        <ScoreBadge score={projectionData.projected_score} projected />
      </div>
    </div>
  );
}
```

### 6.4 Projection Avatar Visual Differences

The projected avatar should look distinct from the current state:

```javascript
const projectionEffects = {
  // Base differences
  opacity: 0.7,                    // Slightly transparent
  saturation: 0.8,                 // Slightly desaturated
  
  // Hologram effect
  hologramLines: true,             // Horizontal scan lines
  hologramLineSpacing: 0.005,      // Gap between lines
  hologramFlicker: true,           // Subtle opacity flicker
  hologramFlickerRate: 0.1,        // Flicker frequency
  
  // Edge glow
  edgeGlow: true,
  edgeGlowColor: '#60a5fa',        // Blue holographic edge
  edgeGlowIntensity: 0.5,
  
  // Floating effect
  floatAnimation: true,
  floatAmplitude: 0.02,            // Subtle up/down float
  floatFrequency: 0.5              // Hz
};
```

**Hologram Shader (GLSL):**
```glsl
// Fragment shader for projection hologram effect
varying vec2 vUv;
uniform float time;
uniform vec3 zoneColor;
uniform float opacity;

void main() {
  // Scan lines
  float scanLine = sin(vUv.y * 500.0) * 0.5 + 0.5;
  scanLine = step(0.5, scanLine);
  
  // Flicker
  float flicker = sin(time * 10.0) * 0.05 + 0.95;
  
  // Edge glow
  float edge = pow(1.0 - abs(dot(vNormal, vec3(0.0, 0.0, 1.0))), 2.0);
  
  vec3 color = zoneColor;
  color += edge * vec3(0.4, 0.6, 1.0); // Blue edge glow
  
  float alpha = opacity * scanLine * flicker;
  
  gl_FragColor = vec4(color, alpha);
}
```

### 6.5 Timeline Slider

Allow users to scrub through projected time:

```jsx
function ProjectionTimeline({ currentScore, projectedScore, days }) {
  const [selectedDay, setSelectedDay] = useState(days);
  
  // Interpolate score based on selected day
  const interpolatedScore = useMemo(() => {
    const progress = selectedDay / days;
    return currentScore + (projectedScore - currentScore) * progress;
  }, [selectedDay, currentScore, projectedScore, days]);
  
  return (
    <div className="projection-timeline">
      <input
        type="range"
        min={0}
        max={days}
        value={selectedDay}
        onChange={(e) => setSelectedDay(Number(e.target.value))}
        className="w-full"
      />
      
      <div className="flex justify-between text-sm">
        <span>Today ({currentScore})</span>
        <span>Day {selectedDay} ({interpolatedScore.toFixed(1)})</span>
        <span>{days} days ({projectedScore})</span>
      </div>
      
      {/* Avatar updates in real-time as slider moves */}
    </div>
  );
}
```

### 6.6 Animated Zone Transition

When showing projection, animate the avatar transitioning between zones:

```javascript
// Smooth transition between current and projected state
function animateZoneTransition(startZone, endZone, duration = 3000) {
  const startColor = ZONE_COLORS[startZone];
  const endColor = ZONE_COLORS[endZone];
  
  return {
    // Color interpolation
    color: {
      from: startColor.primary,
      to: endColor.primary,
      duration,
      easing: 'easeInOutQuad'
    },
    
    // Particle system transition
    particles: {
      count: { from: particleConfig[startZone].count, to: particleConfig[endZone].count },
      speed: { from: particleConfig[startZone].speed, to: particleConfig[endZone].speed },
      duration: duration * 0.8
    },
    
    // Glow intensity
    glow: {
      from: startColor.intensity,
      to: endColor.intensity,
      duration
    }
  };
}
```

---

## 7. Real-Time Data Flow

### 7.1 Data Streaming Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Hardware   │────▶│   Backend    │────▶│   Frontend   │
│   Sensors    │     │   /reading   │     │   3D Avatar  │
└──────────────┘     └──────────────┘     └──────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │   Database   │
                     │   (SQLite)   │
                     └──────────────┘
```

### 7.2 Polling Strategy

Since we're using REST (not WebSockets), implement efficient polling:

```javascript
// Recommended polling interval: 2 seconds
const POLL_INTERVAL = 2000;

function useRealtimeScore(sessionId) {
  const [data, setData] = useState(null);
  
  useEffect(() => {
    if (!sessionId) return;
    
    const poll = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/score/${sessionId}`);
        const newData = await response.json();
        setData(newData);
      } catch (error) {
        console.error('Polling error:', error);
      }
    };
    
    // Initial fetch
    poll();
    
    // Set up interval
    const interval = setInterval(poll, POLL_INTERVAL);
    
    return () => clearInterval(interval);
  }, [sessionId]);
  
  return data;
}
```

### 7.3 Smooth Transitions

When score updates, animate smoothly rather than jumping:

```javascript
function useAnimatedScore(targetScore) {
  const [displayScore, setDisplayScore] = useState(targetScore);
  
  useEffect(() => {
    if (targetScore === null) return;
    
    const startScore = displayScore;
    const diff = targetScore - startScore;
    const duration = 500; // ms
    const startTime = Date.now();
    
    const animate = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = easeOutQuad(progress);
      
      setDisplayScore(startScore + diff * eased);
      
      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };
    
    requestAnimationFrame(animate);
  }, [targetScore]);
  
  return displayScore;
}

function easeOutQuad(t) {
  return t * (2 - t);
}
```

---

## 8. UI Components

### 8.1 Score Display

```jsx
function ScoreDisplay({ score, zone }) {
  const animatedScore = useAnimatedScore(score);
  const zoneConfig = ZONE_COLORS[zone];
  
  return (
    <div 
      className="score-display"
      style={{ 
        '--zone-color': zoneConfig.primary,
        '--zone-glow': zoneConfig.glow 
      }}
    >
      <div className="score-value">
        {animatedScore.toFixed(1)}
      </div>
      <div className="score-zone">
        <span className="zone-emoji">{getZoneEmoji(zone)}</span>
        <span className="zone-label">{zoneConfig.label}</span>
      </div>
    </div>
  );
}
```

**CSS:**
```css
.score-display {
  text-align: center;
  padding: 2rem;
  border-radius: 1rem;
  background: linear-gradient(
    135deg,
    rgba(0, 0, 0, 0.8),
    rgba(0, 0, 0, 0.6)
  );
  box-shadow: 
    0 0 40px var(--zone-glow),
    inset 0 0 20px rgba(255, 255, 255, 0.1);
}

.score-value {
  font-size: 4rem;
  font-weight: bold;
  color: var(--zone-color);
  text-shadow: 0 0 20px var(--zone-glow);
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.02); }
}
```

### 8.2 Component Gauges

```jsx
function ComponentGauge({ name, value, score, weight }) {
  return (
    <div className="component-gauge">
      <div className="gauge-header">
        <span className="component-name">{name}</span>
        <span className="component-weight">{weight}%</span>
      </div>
      
      <div className="gauge-visual">
        <svg viewBox="0 0 100 100" className="gauge-svg">
          {/* Background arc */}
          <circle
            cx="50" cy="50" r="40"
            fill="none"
            stroke="#333"
            strokeWidth="8"
            strokeDasharray="251.2"
            strokeDashoffset="62.8"
            transform="rotate(135 50 50)"
          />
          {/* Value arc */}
          <circle
            cx="50" cy="50" r="40"
            fill="none"
            stroke={getScoreColor(score)}
            strokeWidth="8"
            strokeDasharray="251.2"
            strokeDashoffset={251.2 - (score / 100 * 188.4)}
            transform="rotate(135 50 50)"
            className="gauge-value-arc"
          />
        </svg>
        <div className="gauge-center">
          <span className="gauge-score">{score.toFixed(0)}</span>
          <span className="gauge-value">{value.toFixed(1)}</span>
        </div>
      </div>
    </div>
  );
}
```

### 8.3 AI Nudge Toast

```jsx
function NudgeToast({ sessionId }) {
  const [nudge, setNudge] = useState(null);
  const [visible, setVisible] = useState(false);
  
  const fetchNudge = async () => {
    const response = await fetch(`${API_BASE}/api/nudge/${sessionId}`);
    const data = await response.json();
    setNudge(data);
    setVisible(true);
    
    // Auto-hide after 10 seconds
    setTimeout(() => setVisible(false), 10000);
  };
  
  if (!visible || !nudge) return null;
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 50 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 50 }}
      className="nudge-toast"
      style={{ borderColor: ZONE_COLORS[nudge.zone].primary }}
    >
      <div className="nudge-icon">💡</div>
      <div className="nudge-content">
        <p className="nudge-message">{nudge.message}</p>
        <span className="nudge-zone">{nudge.zone_label}</span>
      </div>
      <button onClick={() => setVisible(false)} className="nudge-close">×</button>
    </motion.div>
  );
}
```

---

## 9. History & Charts

### 9.1 Score History Chart

```jsx
import { LineChart, Line, XAxis, YAxis, Tooltip, ReferenceLine } from 'recharts';

function ScoreHistoryChart({ sessionId }) {
  const [history, setHistory] = useState([]);
  
  useEffect(() => {
    fetch(`${API_BASE}/api/history/${sessionId}`)
      .then(r => r.json())
      .then(setHistory);
  }, [sessionId]);
  
  return (
    <div className="history-chart">
      <LineChart width={600} height={300} data={history}>
        {/* Zone threshold lines */}
        <ReferenceLine y={80} stroke="#22c55e" strokeDasharray="3 3" label="Thriving" />
        <ReferenceLine y={55} stroke="#eab308" strokeDasharray="3 3" label="Mild" />
        <ReferenceLine y={30} stroke="#f97316" strokeDasharray="3 3" label="Moderate" />
        
        <XAxis dataKey="index" />
        <YAxis domain={[0, 100]} />
        <Tooltip content={<CustomTooltip />} />
        
        <Line
          type="monotone"
          dataKey="score"
          stroke="#60a5fa"
          strokeWidth={2}
          dot={false}
          animationDuration={500}
        />
      </LineChart>
    </div>
  );
}

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.[0]) return null;
  
  const data = payload[0].payload;
  return (
    <div className="chart-tooltip">
      <p className="score">{data.score.toFixed(1)}</p>
      <p className="zone" style={{ color: ZONE_COLORS[data.zone].primary }}>
        {data.zone_label}
      </p>
    </div>
  );
}
```

---

## 10. Alert System

### 10.1 Emergency Alert Modal

```jsx
function EmergencyAlertModal({ sessionId, score, zone, onClose }) {
  const [phone, setPhone] = useState('');
  const [channel, setChannel] = useState('whatsapp');
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);
  
  const sendAlert = async () => {
    setSending(true);
    
    await fetch(`${API_BASE}/api/alert`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        phone,
        channel
      })
    });
    
    setSending(false);
    setSent(true);
  };
  
  return (
    <Modal isOpen onClose={onClose}>
      <div className="alert-modal">
        <h2>🚨 Send Emergency Alert</h2>
        
        <div className="alert-preview" style={{ background: ZONE_COLORS[zone].ambient }}>
          <p>Score: <strong>{score.toFixed(1)}</strong></p>
          <p>Status: <strong>{ZONE_COLORS[zone].label}</strong></p>
        </div>
        
        <input
          type="tel"
          placeholder="+1234567890"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
        />
        
        <div className="channel-selector">
          <button 
            className={channel === 'whatsapp' ? 'active' : ''}
            onClick={() => setChannel('whatsapp')}
          >
            WhatsApp
          </button>
          <button 
            className={channel === 'sms' ? 'active' : ''}
            onClick={() => setChannel('sms')}
          >
            SMS
          </button>
        </div>
        
        <button 
          onClick={sendAlert} 
          disabled={sending || !phone}
          className="send-alert-btn"
        >
          {sending ? 'Sending...' : sent ? '✓ Sent!' : 'Send Alert'}
        </button>
      </div>
    </Modal>
  );
}
```

---

## 11. Mobile Responsiveness

### 11.1 Responsive Layout

```jsx
function Dashboard() {
  const isMobile = useMediaQuery('(max-width: 768px)');
  
  return (
    <div className={`dashboard ${isMobile ? 'mobile' : 'desktop'}`}>
      {isMobile ? (
        // Mobile: Stack vertically
        <div className="mobile-layout">
          <div className="avatar-section">
            <AvatarViewer size="small" />
          </div>
          <div className="score-section">
            <ScoreDisplay />
          </div>
          <div className="components-section">
            <ComponentGauges layout="horizontal" />
          </div>
        </div>
      ) : (
        // Desktop: Side by side
        <div className="desktop-layout">
          <div className="left-panel">
            <AvatarViewer size="large" />
          </div>
          <div className="right-panel">
            <ScoreDisplay />
            <ComponentGauges layout="grid" />
            <HistoryChart />
          </div>
        </div>
      )}
    </div>
  );
}
```

### 11.2 Touch Gestures for 3D Avatar

```jsx
import { OrbitControls } from '@react-three/drei';

function MobileAvatarViewer({ zone, score }) {
  return (
    <Canvas>
      <OrbitControls
        enablePan={false}
        enableZoom={true}
        minDistance={1.5}
        maxDistance={4}
        minPolarAngle={Math.PI / 4}
        maxPolarAngle={Math.PI / 2}
        touches={{
          ONE: THREE.TOUCH.ROTATE,
          TWO: THREE.TOUCH.DOLLY_PAN
        }}
      />
      <Avatar zone={zone} score={score} />
    </Canvas>
  );
}
```

---

## 12. Performance Optimization

### 12.1 3D Optimization

```javascript
// LOD (Level of Detail) for avatar
const LOD_CONFIGS = {
  high: { distance: 0, polygons: 30000 },
  medium: { distance: 5, polygons: 15000 },
  low: { distance: 10, polygons: 5000 }
};

// Reduce particle count on mobile
const getParticleCount = (zone, isMobile) => {
  const baseCount = particleConfig[zone].count;
  return isMobile ? Math.floor(baseCount * 0.5) : baseCount;
};

// Disable shadows on mobile
const SHADOW_ENABLED = !isMobile;
```

### 12.2 Data Caching

```javascript
import { useQuery } from '@tanstack/react-query';

function useScore(sessionId) {
  return useQuery({
    queryKey: ['score', sessionId],
    queryFn: () => fetch(`${API_BASE}/api/score/${sessionId}`).then(r => r.json()),
    refetchInterval: 2000,
    staleTime: 1000,
  });
}

function useHistory(sessionId) {
  return useQuery({
    queryKey: ['history', sessionId],
    queryFn: () => fetch(`${API_BASE}/api/history/${sessionId}`).then(r => r.json()),
    refetchInterval: 5000,
    staleTime: 3000,
  });
}
```

---

## 13. Accessibility

### 13.1 Screen Reader Support

```jsx
function ScoreDisplay({ score, zone }) {
  return (
    <div 
      role="status" 
      aria-live="polite"
      aria-label={`CardioTwin Score: ${score.toFixed(1)}. Status: ${ZONE_COLORS[zone].label}`}
    >
      {/* Visual content */}
    </div>
  );
}
```

### 13.2 Color Blind Support

Provide patterns/icons in addition to colors:

```javascript
const ZONE_PATTERNS = {
  GREEN: { icon: '✓', pattern: 'solid' },
  YELLOW: { icon: '!', pattern: 'dashed' },
  ORANGE: { icon: '⚠', pattern: 'dotted' },
  RED: { icon: '✕', pattern: 'zigzag' }
};
```

---

## 14. Testing Checklist

### 14.1 Unit Tests
- [ ] Zone color mapping
- [ ] Score interpolation
- [ ] Component gauge calculations

### 14.2 Integration Tests
- [ ] Session start flow
- [ ] Calibration progress updates
- [ ] Score polling and display
- [ ] History chart rendering
- [ ] Alert sending

### 14.3 Visual Tests
- [ ] Avatar renders in all zones
- [ ] Particle effects visible
- [ ] Heart glow animation smooth
- [ ] Zone transitions animate correctly
- [ ] Projection mode comparison view

### 14.4 Performance Tests
- [ ] 60 FPS on desktop
- [ ] 30+ FPS on mobile
- [ ] Memory usage stable over time
- [ ] No WebGL warnings/errors

---

## 15. Deployment Considerations

### 15.1 Environment Variables
```env
NEXT_PUBLIC_API_BASE=https://cardiotwin-jqrct.ondigitalocean.app
```

### 15.2 CORS
The backend already allows all origins (`*`), so no additional configuration needed.

### 15.3 Asset Hosting
Host 3D models on CDN for fast loading:
- GLB files should be < 5MB
- Use Draco compression for meshes
- Preload models during app initialization

---

## 16. Success Metrics

| Metric | Target |
|--------|--------|
| Time to First Score | < 30 seconds (15 calibration readings) |
| Avatar Frame Rate | 60 FPS desktop, 30 FPS mobile |
| API Response Time | < 200ms |
| Score Update Latency | < 500ms perceived |
| User Engagement | > 5 min average session |

---

## Appendix A: Complete React Hook

```javascript
// hooks/useCardioTwin.js
import { useState, useEffect, useCallback, useRef } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'https://cardiotwin-jqrct.ondigitalocean.app';

export function useCardioTwin(userId) {
  const [sessionId, setSessionId] = useState(null);
  const [status, setStatus] = useState('idle');
  const [score, setScore] = useState(null);
  const [zone, setZone] = useState(null);
  const [zoneLabel, setZoneLabel] = useState(null);
  const [calibrationProgress, setCalibrationProgress] = useState(0);
  const [components, setComponents] = useState(null);
  const [baseline, setBaseline] = useState(null);
  const [history, setHistory] = useState([]);
  const [alert, setAlert] = useState(false);
  
  const pollingRef = useRef(null);

  const startSession = useCallback(async () => {
    const newSessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    
    const response = await fetch(`${API_BASE}/api/session/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: newSessionId, user_id: userId })
    });
    
    if (response.ok) {
      setSessionId(newSessionId);
      setStatus('calibrating');
      setCalibrationProgress(0);
    }
    
    return newSessionId;
  }, [userId]);

  const submitReading = useCallback(async (bpm, hrv, spo2, temperature) => {
    if (!sessionId) throw new Error('No active session');
    
    const response = await fetch(`${API_BASE}/api/reading`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, bpm, hrv, spo2, temperature })
    });
    
    const data = await response.json();

    if (data.status === 'calibrating') {
      setStatus('calibrating');
      setCalibrationProgress(data.readings_collected / data.readings_needed);
    } else if (data.status === 'scored') {
      setStatus('ready');
      setScore(data.score);
      setZone(data.zone);
      setZoneLabel(data.zone_label);
      setComponents(data.components);
      setBaseline(data.baseline);
      setAlert(data.alert);
    }
    
    return data;
  }, [sessionId]);

  const fetchHistory = useCallback(async () => {
    if (!sessionId) return [];
    
    const response = await fetch(`${API_BASE}/api/history/${sessionId}`);
    const data = await response.json();
    setHistory(data);
    return data;
  }, [sessionId]);

  const getNudge = useCallback(async () => {
    if (!sessionId) return null;
    
    const response = await fetch(`${API_BASE}/api/nudge/${sessionId}`);
    return response.json();
  }, [sessionId]);

  const getProjection = useCallback(async (days = 30) => {
    if (!sessionId) return null;
    
    const response = await fetch(`${API_BASE}/api/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, days })
    });
    
    return response.json();
  }, [sessionId]);

  const sendAlert = useCallback(async (phone, channel = 'whatsapp') => {
    if (!sessionId) return null;
    
    const response = await fetch(`${API_BASE}/api/alert`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, phone, channel })
    });
    
    return response.json();
  }, [sessionId]);

  const endSession = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
    }
    setSessionId(null);
    setStatus('idle');
    setScore(null);
    setZone(null);
    setCalibrationProgress(0);
    setComponents(null);
    setBaseline(null);
    setHistory([]);
  }, []);

  return {
    // State
    sessionId,
    status,
    score,
    zone,
    zoneLabel,
    calibrationProgress,
    components,
    baseline,
    history,
    alert,
    
    // Actions
    startSession,
    submitReading,
    fetchHistory,
    getNudge,
    getProjection,
    sendAlert,
    endSession
  };
}
```

---

## Appendix B: Zone Colors CSS Variables

```css
:root {
  /* Green Zone */
  --zone-green-primary: #22c55e;
  --zone-green-glow: #4ade80;
  --zone-green-particle: #86efac;
  --zone-green-ambient: #dcfce7;
  
  /* Yellow Zone */
  --zone-yellow-primary: #eab308;
  --zone-yellow-glow: #facc15;
  --zone-yellow-particle: #fde047;
  --zone-yellow-ambient: #fef9c3;
  
  /* Orange Zone */
  --zone-orange-primary: #f97316;
  --zone-orange-glow: #fb923c;
  --zone-orange-particle: #fdba74;
  --zone-orange-ambient: #ffedd5;
  
  /* Red Zone */
  --zone-red-primary: #ef4444;
  --zone-red-glow: #f87171;
  --zone-red-particle: #fca5a5;
  --zone-red-ambient: #fee2e2;
}
```

---

## Contact & Resources

- **Backend API:** https://cardiotwin-jqrct.ondigitalocean.app
- **OpenAPI Docs:** https://cardiotwin-jqrct.ondigitalocean.app/docs
- **API Documentation:** [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
- **GitHub Repo:** https://github.com/Techdee1/Kardio-Twin

---

*Document Version 1.0 | February 21, 2026*
