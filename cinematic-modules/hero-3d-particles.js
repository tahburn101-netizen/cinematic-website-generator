/**
 * CINEMATIC MODULE: 3D Particle Hero
 * Source inspiration: motionsites.ai "Aetheris Voyage", 21st.dev "Neon Flow", Three.js
 * 
 * Creates a full-screen 3D particle field that:
 * - Reacts to scroll (particles disperse/converge as user scrolls)
 * - Has depth and parallax
 * - Morphs between shapes based on brand niche
 * - Fully GPU-accelerated via Three.js WebGL
 */

(function initCinematicHero3D(config) {
  const {
    containerId = 'hero-3d-canvas',
    accentColor = '#e63946',
    secondaryColor = '#ffffff',
    backgroundColor = '#0d0d0d',
    particleCount = 3000,
    niche = 'business'
  } = config || {};

  // Niche-specific particle behaviors
  const NICHE_CONFIGS = {
    restaurant: { shape: 'sphere', speed: 0.3, size: 0.015, spread: 3.5 },
    fitness: { shape: 'torus', speed: 0.8, size: 0.012, spread: 4.0 },
    beauty: { shape: 'heart', speed: 0.2, size: 0.018, spread: 3.0 },
    real_estate: { shape: 'grid', speed: 0.15, size: 0.01, spread: 5.0 },
    tech_saas: { shape: 'dna', speed: 0.6, size: 0.01, spread: 4.5 },
    ecommerce: { shape: 'sphere', speed: 0.25, size: 0.016, spread: 3.5 },
    agency: { shape: 'wave', speed: 0.4, size: 0.014, spread: 4.0 },
    medical: { shape: 'grid', speed: 0.2, size: 0.01, spread: 4.5 },
    hotel: { shape: 'sphere', speed: 0.15, size: 0.02, spread: 3.0 },
    law: { shape: 'grid', speed: 0.1, size: 0.012, spread: 5.0 },
    business: { shape: 'wave', speed: 0.3, size: 0.013, spread: 4.0 }
  };

  const nicheConf = NICHE_CONFIGS[niche] || NICHE_CONFIGS.business;

  function hexToRgb(hex) {
    const r = parseInt(hex.slice(1, 3), 16) / 255;
    const g = parseInt(hex.slice(3, 5), 16) / 255;
    const b = parseInt(hex.slice(5, 7), 16) / 255;
    return { r, g, b };
  }

  function loadThreeJS(callback) {
    if (window.THREE) { callback(); return; }
    const script = document.createElement('script');
    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js';
    script.onload = callback;
    document.head.appendChild(script);
  }

  function init() {
    const container = document.getElementById(containerId);
    if (!container) return;

    const THREE = window.THREE;
    const W = container.clientWidth;
    const H = container.clientHeight;

    // Scene setup
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, W / H, 0.1, 100);
    camera.position.z = 3;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(W, H);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x000000, 0);
    container.appendChild(renderer.domElement);

    // Particle geometry
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);
    const sizes = new Float32Array(particleCount);
    const velocities = new Float32Array(particleCount * 3);

    const accent = hexToRgb(accentColor);
    const secondary = hexToRgb(secondaryColor);

    for (let i = 0; i < particleCount; i++) {
      const i3 = i * 3;
      const spread = nicheConf.spread;

      // Generate positions based on niche shape
      let x, y, z;
      if (nicheConf.shape === 'sphere') {
        const theta = Math.random() * Math.PI * 2;
        const phi = Math.acos(2 * Math.random() - 1);
        const r = spread * (0.5 + Math.random() * 0.5);
        x = r * Math.sin(phi) * Math.cos(theta);
        y = r * Math.sin(phi) * Math.sin(theta);
        z = r * Math.cos(phi);
      } else if (nicheConf.shape === 'wave') {
        x = (Math.random() - 0.5) * spread * 2;
        y = Math.sin(x * 0.5) * 1.5 + (Math.random() - 0.5) * 2;
        z = (Math.random() - 0.5) * spread;
      } else if (nicheConf.shape === 'dna') {
        const t = (i / particleCount) * Math.PI * 8;
        x = Math.cos(t) * 1.5 + (Math.random() - 0.5) * 0.3;
        y = (t / (Math.PI * 8)) * spread - spread / 2;
        z = Math.sin(t) * 1.5 + (Math.random() - 0.5) * 0.3;
      } else if (nicheConf.shape === 'torus') {
        const theta = Math.random() * Math.PI * 2;
        const phi = Math.random() * Math.PI * 2;
        const R = 2, r = 0.8;
        x = (R + r * Math.cos(phi)) * Math.cos(theta);
        y = (R + r * Math.cos(phi)) * Math.sin(theta);
        z = r * Math.sin(phi);
      } else {
        // grid
        x = (Math.random() - 0.5) * spread * 2;
        y = (Math.random() - 0.5) * spread * 1.5;
        z = (Math.random() - 0.5) * spread;
      }

      positions[i3] = x;
      positions[i3 + 1] = y;
      positions[i3 + 2] = z;

      // Color: mix accent and secondary based on position
      const mix = Math.random();
      colors[i3] = accent.r * mix + secondary.r * (1 - mix);
      colors[i3 + 1] = accent.g * mix + secondary.g * (1 - mix);
      colors[i3 + 2] = accent.b * mix + secondary.b * (1 - mix);

      sizes[i] = nicheConf.size * (0.5 + Math.random());
      velocities[i3] = (Math.random() - 0.5) * 0.002;
      velocities[i3 + 1] = (Math.random() - 0.5) * 0.002;
      velocities[i3 + 2] = (Math.random() - 0.5) * 0.001;
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));

    // Shader material for glowing particles
    const material = new THREE.ShaderMaterial({
      uniforms: {
        time: { value: 0 },
        scroll: { value: 0 },
        pixelRatio: { value: renderer.getPixelRatio() }
      },
      vertexShader: `
        attribute float size;
        attribute vec3 color;
        varying vec3 vColor;
        uniform float time;
        uniform float scroll;
        uniform float pixelRatio;
        
        void main() {
          vColor = color;
          vec3 pos = position;
          
          // Scroll-driven dispersion
          float disperse = scroll * 2.0;
          pos.x += sin(pos.y * 2.0 + time * 0.5) * disperse * 0.3;
          pos.y += cos(pos.x * 2.0 + time * 0.3) * disperse * 0.2;
          pos.z += sin(time * 0.4 + pos.x) * 0.1;
          
          // Gentle float animation
          pos.y += sin(time * 0.5 + pos.x * 3.0) * 0.05;
          pos.x += cos(time * 0.3 + pos.z * 2.0) * 0.03;
          
          vec4 mvPosition = modelViewMatrix * vec4(pos, 1.0);
          gl_PointSize = size * pixelRatio * (300.0 / -mvPosition.z);
          gl_Position = projectionMatrix * mvPosition;
        }
      `,
      fragmentShader: `
        varying vec3 vColor;
        
        void main() {
          float dist = length(gl_PointCoord - vec2(0.5));
          if (dist > 0.5) discard;
          
          // Soft glow
          float alpha = 1.0 - smoothstep(0.0, 0.5, dist);
          alpha = pow(alpha, 1.5);
          
          gl_FragColor = vec4(vColor, alpha * 0.85);
        }
      `,
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      vertexColors: true
    });

    const particles = new THREE.Points(geometry, material);
    scene.add(particles);

    // Scroll tracking
    let scrollY = 0;
    let targetScrollY = 0;
    window.addEventListener('scroll', () => {
      targetScrollY = window.scrollY / window.innerHeight;
    });

    // Mouse parallax
    let mouseX = 0, mouseY = 0;
    document.addEventListener('mousemove', (e) => {
      mouseX = (e.clientX / window.innerWidth - 0.5) * 2;
      mouseY = -(e.clientY / window.innerHeight - 0.5) * 2;
    });

    // Animation loop
    let time = 0;
    function animate() {
      requestAnimationFrame(animate);
      time += 0.01 * nicheConf.speed;
      scrollY += (targetScrollY - scrollY) * 0.05;

      material.uniforms.time.value = time;
      material.uniforms.scroll.value = scrollY;

      // Camera parallax on mouse
      camera.position.x += (mouseX * 0.3 - camera.position.x) * 0.05;
      camera.position.y += (mouseY * 0.2 - camera.position.y) * 0.05;
      camera.lookAt(scene.position);

      // Rotate particle system
      particles.rotation.y = time * 0.05 * nicheConf.speed;
      particles.rotation.x = Math.sin(time * 0.03) * 0.1;

      renderer.render(scene, camera);
    }
    animate();

    // Resize handler
    window.addEventListener('resize', () => {
      const W = container.clientWidth;
      const H = container.clientHeight;
      camera.aspect = W / H;
      camera.updateProjectionMatrix();
      renderer.setSize(W, H);
    });
  }

  loadThreeJS(init);

})(window.__HERO_CONFIG__ || {});
