'use client'

import { Suspense, useState, useCallback, useMemo, useEffect } from 'react'
import { Canvas, useThree } from '@react-three/fiber'
import { OrbitControls, PerspectiveCamera } from '@react-three/drei'
import LowPolyBrain from './LowPolyBrain'

// ── Default proficiency levels (fallback when no data) ──────────
const DEFAULT_PROFICIENCY: Record<string, number> = {
  Region_Fundamentals:  0.0,
  Region_OOP:           0.0,
  Region_DataStructures:0.0,
  Region_Algorithms:    0.0,
  Region_Systems:       0.0,
  Region_Frontend:      0.0,
  Region_DevPractices:  0.0,
  Region_Product:       0.0,
  Region_Hackathon:     0.0,
}

// ── Responsive camera hook ──────────
function useResponsiveCamera() {
  const [cameraZ, setCameraZ] = useState(3.8)
  
  useEffect(() => {
    const updateCamera = () => {
      const width = window.innerWidth
      const height = window.innerHeight
      const aspectRatio = width / height
      
      // Adjust camera distance based on screen size
      // Smaller screens = further camera = smaller brain
      if (width < 480) {
        setCameraZ(5.5) // Very small mobile
      } else if (width < 640) {
        setCameraZ(5.0) // Mobile
      } else if (width < 768) {
        setCameraZ(4.5) // Large mobile / small tablet
      } else if (width < 1024) {
        setCameraZ(4.2) // Tablet
      } else if (aspectRatio < 1.2) {
        setCameraZ(4.5) // Tall/portrait screens
      } else {
        setCameraZ(3.8) // Desktop
      }
    }
    
    updateCamera()
    window.addEventListener('resize', updateCamera)
    return () => window.removeEventListener('resize', updateCamera)
  }, [])
  
  return cameraZ
}

export interface BrainSceneProps {
  proficiencyLevels?: Record<string, number>
  triggerAnimation?: boolean
  onRegionClick?: (regionId: string) => void
}

function Scene({
  activeRegions,
  proficiencyLevels,
  triggerAnimation,
  onRegionHover,
  onRegionClick,
  cameraZ,
}: {
  activeRegions?: Set<string>
  proficiencyLevels?: Record<string, number>
  triggerAnimation?: boolean
  onRegionHover?: (id: string | null) => void
  onRegionClick?: (id: string) => void
  cameraZ: number
}) {
  return (
    <>
      <PerspectiveCamera makeDefault position={[0, 0.3, cameraZ]} fov={45} />

      <ambientLight intensity={0.35} />
      <directionalLight position={[5, 5, 5]} intensity={0.4} color="#ffffff" />
      <directionalLight position={[-5, 3, -5]} intensity={0.25} color="#6366f1" />
      <pointLight position={[0, 2, 4]} intensity={0.3} color="#60a5fa" />

      <Suspense fallback={null}>
        <LowPolyBrain
          activeRegions={activeRegions}
          proficiencyLevels={proficiencyLevels}
          triggerAnimation={triggerAnimation}
          onRegionHover={onRegionHover}
          onRegionClick={onRegionClick}
        />
      </Suspense>

      <OrbitControls
        enableZoom={false}
        enablePan={false}
        enableRotate={true}
        autoRotate
        autoRotateSpeed={0.8}
        enableDamping
        dampingFactor={0.08}
      />


    </>
  )
}

export default function BrainScene({ 
  proficiencyLevels,
  triggerAnimation,
  onRegionClick: externalOnRegionClick,
}: BrainSceneProps = {}) {
  const [hoveredRegion, setHoveredRegion] = useState<string | null>(null)
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 })
  const cameraZ = useResponsiveCamera()

  // Track mouse position for tooltip
  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    setMousePos({ x: e.clientX, y: e.clientY })
  }, [])

  // Merge provided proficiency with defaults
  const mergedProficiency = useMemo(() => ({
    ...DEFAULT_PROFICIENCY,
    ...proficiencyLevels,
  }), [proficiencyLevels])

  // Don't restrict active regions on hover — the hover highlight is handled
  // internally by LowPolyBrain's own hoveredRegion state. Setting activeRegions
  // here would dim all other regions and wipe out the proficiency glow.
  const activeRegions = undefined

  const handleRegionHover = useCallback((id: string | null) => {
    setHoveredRegion(id)
  }, [])

  const handleRegionClick = useCallback((id: string) => {
    console.log('Region clicked:', id)
    externalOnRegionClick?.(id)
  }, [externalOnRegionClick])

  return (
    <div className="canvas-container" onMouseMove={handleMouseMove}>
      <Canvas
        gl={{
          antialias: true,
          alpha: true,
          powerPreference: 'high-performance',
        }}
        style={{ background: '#000000' }}
      >
        <Scene
          activeRegions={activeRegions}
          proficiencyLevels={mergedProficiency}
          triggerAnimation={triggerAnimation}
          onRegionHover={handleRegionHover}
          onRegionClick={handleRegionClick}
          cameraZ={cameraZ}
        />
      </Canvas>


    </div>
  )
}
