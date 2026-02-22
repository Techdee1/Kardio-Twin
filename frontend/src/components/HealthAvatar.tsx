import { useGLTF, Html } from '@react-three/drei';
import { useFrame } from '@react-three/fiber';
import { useRef, useMemo } from 'react';
import * as THREE from 'three';
import { Heart, Wind, ThermometerSun, Activity } from 'lucide-react';

export function HealthAvatar({ score, vitals }: { score: number, vitals: any }) {
  // Load the optimized 14MB model
  const { scene } = useGLTF(
    '/models/avatar.glb',
    'https://www.gstatic.com/draco/versioned/decoders/1.5.7/'
  );

  const lightRef = useRef<THREE.PointLight>(null);

  const zoneColor = useMemo(() => {
    if (score >= 80) return '#22c55e';
    if (score >= 55) return '#eab308';
    if (score >= 30) return '#f97316';
    return '#ef4444';
  }, [score]);

  useFrame(({ clock }) => {
    const t = clock.getElapsedTime();

    if (lightRef.current) {
      const bpmSync = ((vitals?.heartRate || 60) / 60) * Math.PI * 2;
      const intensity = 2 + Math.sin(t * bpmSync) * 1.5;
      lightRef.current.intensity = intensity;
    }
  });

  return (
    <group position={[0, -1.8, 0]}>
      <primitive object={scene} scale={2.5} />
      <pointLight
        ref={lightRef}
        position={[-0.2, 3.2, 0.2]}
        color={zoneColor}
        distance={3}
        decay={2}
      />

      <Html position={[-0.18, 3.18, 0.55]} transform sprite center scale={0.2} zIndexRange={[100, 0]}>
        <div className="flex flex-col items-center group cursor-pointer transition-transform hover:scale-110">
          <div className="w-6 h-6 rounded-full bg-rose-500/20 flex items-center justify-center animate-ping absolute border border-rose-500/50"></div>
          <div className="w-3.5 h-3.5 rounded-full bg-rose-500 relative z-10 shadow-[0_0_15px_rgba(244,63,94,0.8)]"></div>

          <div className="absolute top-1/2 left-8 -translate-y-1/2 bg-white/95 backdrop-blur-md px-5 py-4 rounded-2xl shadow-xl border border-rose-500/20 w-44 overflow-hidden pointer-events-auto">
            <div className="absolute top-0 left-0 w-1.5 h-full bg-rose-500"></div>
            <div className="flex items-center gap-2 mb-2">
              <Heart className="w-5 h-5 text-rose-500 fill-rose-500/20 animate-pulse" />
              <span className="text-[11px] font-bold text-background-dark/50 uppercase tracking-widest block">Heart Rate</span>
            </div>
            <div className="text-4xl font-black text-background-dark tabular-nums tracking-tighter">{vitals.heartRate}<span className="text-sm font-bold text-background-dark/40 ml-1">bpm</span></div>
          </div>
        </div>
      </Html>

      {/* SpO2 - Right Wrist */}
      <Html position={[-1.05, 2.22, 0.15]} transform sprite center scale={0.2} zIndexRange={[100, 0]}>
        <div className="flex flex-col items-center group cursor-pointer transition-transform hover:scale-110">
          <div className="w-6 h-6 rounded-full bg-cyan-500/20 flex items-center justify-center animate-ping absolute border border-cyan-500/50"></div>
          <div className="w-3.5 h-3.5 rounded-full bg-cyan-500 relative z-10 shadow-[0_0_15px_rgba(6,182,212,0.8)]"></div>

          <div className="absolute top-1/2 right-8 -translate-y-1/2 bg-white/95 backdrop-blur-md px-5 py-4 rounded-2xl shadow-xl border border-cyan-500/20 w-44 overflow-hidden pointer-events-auto">
            <div className="absolute top-0 right-0 w-1.5 h-full bg-cyan-500"></div>
            <div className="flex items-center justify-end gap-2 mb-2">
              <span className="text-[11px] font-bold text-background-dark/50 uppercase tracking-widest block">SpO<sub>2</sub></span>
              <Wind className="w-5 h-5 text-cyan-500" />
            </div>
            <div className="text-4xl font-black text-background-dark tabular-nums text-right tracking-tighter">{vitals.spO2}<span className="text-sm font-bold text-background-dark/40 ml-1">%</span></div>
          </div>
        </div>
      </Html>

      {/* Skin Temp - Forehead */}
      <Html position={[-0.45, 4.20, 0.5]} transform sprite center scale={0.2} zIndexRange={[100, 0]}>
        <div className="flex flex-col items-center group cursor-pointer transition-transform hover:scale-110">
          <div className="w-6 h-6 rounded-full bg-orange-500/20 flex items-center justify-center animate-ping absolute border border-orange-500/50"></div>
          <div className="w-3.5 h-3.5 rounded-full bg-orange-500 relative z-10 shadow-[0_0_15px_rgba(249,115,22,0.8)]"></div>

          <div className="absolute bottom-6 left-1/2 -translate-x-1/2 bg-white/95 backdrop-blur-md px-5 py-4 rounded-2xl shadow-xl border border-orange-500/20 w-44 overflow-hidden pointer-events-auto">
            <div className="absolute top-0 left-0 w-full h-1.5 bg-orange-500"></div>
            <div className="flex items-center gap-2 mb-2">
              <ThermometerSun className="w-5 h-5 text-orange-500" />
              <span className="text-[11px] font-bold text-background-dark/50 uppercase tracking-widest block">Core Temp</span>
            </div>
            <div className="text-4xl font-black text-background-dark tabular-nums tracking-tighter">{vitals.skinTemp?.toFixed(1)}<span className="text-sm font-bold text-background-dark/40 ml-1">°C</span></div>
          </div>
        </div>
      </Html>

      {/* HRV - Center abdomen / solar plexus */}
      <Html position={[-0.45, 2.85, 0.45]} transform sprite center scale={0.2} zIndexRange={[100, 0]}>
        <div className="flex flex-col items-center group cursor-pointer transition-transform hover:scale-110">
          <div className="w-6 h-6 rounded-full bg-blue-500/20 flex items-center justify-center animate-ping absolute border border-blue-500/50"></div>
          <div className="w-3.5 h-3.5 rounded-full bg-blue-500 relative z-10 shadow-[0_0_15px_rgba(59,130,246,0.8)]"></div>

          <div className="absolute top-1/2 right-8 -translate-y-1/2 bg-white/95 backdrop-blur-md px-5 py-4 rounded-2xl shadow-xl border border-blue-500/20 w-44 overflow-hidden pointer-events-auto">
            <div className="absolute top-0 right-0 w-1.5 h-full bg-blue-500"></div>
            <div className="flex items-center justify-end gap-2 mb-2">
              <span className="text-[11px] font-bold text-background-dark/50 uppercase tracking-widest block">Var. (HRV)</span>
              <Activity className="w-5 h-5 text-blue-500" />
            </div>
            <div className="text-4xl font-black text-background-dark tabular-nums text-right tracking-tighter">{vitals.hrv}<span className="text-sm font-bold text-background-dark/40 ml-1">ms</span></div>
          </div>
        </div>
      </Html>

    </group>
  );
}

// Preload the model for faster initial rendering
useGLTF.preload('/models/avatar.glb', 'https://www.gstatic.com/draco/versioned/decoders/1.5.7/');