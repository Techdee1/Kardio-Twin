/// <reference types="vite/client" />

// Extend JSX namespace for React Three Fiber
import type { Object3DNode } from '@react-three/fiber';
import type { AmbientLight, DirectionalLight, PointLight, SpotLight } from 'three';

declare module '@react-three/fiber' {
  interface ThreeElements {
    ambientLight: Object3DNode<AmbientLight, typeof AmbientLight>;
    directionalLight: Object3DNode<DirectionalLight, typeof DirectionalLight>;
    pointLight: Object3DNode<PointLight, typeof PointLight>;
    spotLight: Object3DNode<SpotLight, typeof SpotLight>;
  }
}
