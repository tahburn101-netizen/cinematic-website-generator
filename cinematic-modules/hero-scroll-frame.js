/**
 * CINEMATIC SCROLL-DRIVEN HERO — hero-scroll-frame.js v2
 * =======================================================
 * Reliable scroll-driven Three.js particle hero.
 * Works on mobile (touch) AND desktop.
 * No race conditions. Waits for Three.js via polling.
 * Plays forward on scroll down, reverses on scroll up.
 *
 * Set window.HERO_CONFIG before including this script:
 *   window.HERO_CONFIG = { sectionId, niche, accentColor, bgColorA, bgColorB, scrollMultiplier }
 */
(function () {
  'use strict';

  var cfg = window.HERO_CONFIG || window.__HERO_FRAME_CONFIG__ || {};
  var NICHE       = cfg.niche       || 'default';
  var ACCENT      = cfg.accentColor || cfg.accent || '#6c63ff';
  var BG_A        = cfg.bgColorA    || cfg.bg     || '#09090b';
  var BG_B        = cfg.bgColorB    || '#1a0a2e';
  var SECTION_ID  = cfg.sectionId   || 'hero-scroll-section';
  var SCROLL_MULT = Math.max(2, Math.min(4, cfg.scrollMultiplier || 3));

  /* Niche palettes */
  var PALETTES = {
    restaurant:  { a:'#e8c97a', b:'#c0392b', bg:'#0a0806' },
    coffee:      { a:'#c8552a', b:'#f5e6d0', bg:'#0c0806' },
    cafe:        { a:'#c8552a', b:'#f5e6d0', bg:'#0c0806' },
    fitness:     { a:'#00d4ff', b:'#ff6b35', bg:'#060a0e' },
    gym:         { a:'#00d4ff', b:'#ff6b35', bg:'#060a0e' },
    beauty:      { a:'#e8a0bf', b:'#c77dff', bg:'#0a0610' },
    skincare:    { a:'#e8a0bf', b:'#c77dff', bg:'#0a0610' },
    tech:        { a:'#4fc3f7', b:'#7c4dff', bg:'#050810' },
    saas:        { a:'#4fc3f7', b:'#7c4dff', bg:'#050810' },
    tech_saas:   { a:'#4fc3f7', b:'#7c4dff', bg:'#050810' },
    automotive:  { a:'#ff6b35', b:'#ffd700', bg:'#080604' },
    garage:      { a:'#ff6b35', b:'#ffd700', bg:'#080604' },
    real_estate: { a:'#4caf50', b:'#81c784', bg:'#050a06' },
    hotel:       { a:'#d4af37', b:'#f5e6c8', bg:'#080706' },
    resort:      { a:'#d4af37', b:'#f5e6c8', bg:'#080706' },
    fashion:     { a:'#ff4081', b:'#f8bbd9', bg:'#0a0608' },
    music:       { a:'#ff5722', b:'#ff9800', bg:'#080604' },
    finance:     { a:'#00e676', b:'#69f0ae', bg:'#050a06' },
    law:         { a:'#d4af37', b:'#fff8e1', bg:'#080706' },
    medical:     { a:'#00bcd4', b:'#80deea', bg:'#050a0c' },
    education:   { a:'#ff9800', b:'#ffe082', bg:'#080604' },
    travel:      { a:'#29b6f6', b:'#81d4fa', bg:'#050a0e' },
    photography: { a:'#bdbdbd', b:'#ffffff', bg:'#080808' },
    architecture:{ a:'#78909c', b:'#cfd8dc', bg:'#060808' },
    bakery:      { a:'#ff8a65', b:'#ffccbc', bg:'#0a0806' },
    default:     { a:'#6c63ff', b:'#a78bfa', bg:'#09090b' },
  };

  var PAL = PALETTES[NICHE] || PALETTES['default'];
  if (ACCENT && ACCENT !== '#6c63ff') PAL.a = ACCENT;
  if (BG_A && BG_A !== '#09090b') PAL.bg = BG_A;

  function waitForThree(cb, n) {
    n = n || 0;
    if (window.THREE) { cb(); return; }
    if (n > 100) { console.warn('[HeroFrame] THREE.js not found after 5s'); return; }
    setTimeout(function(){ waitForThree(cb, n+1); }, 50);
  }

  function init() {
    var THREE = window.THREE;
    var section = document.getElementById(SECTION_ID);
    if (!section) { console.warn('[HeroFrame] section not found:', SECTION_ID); return; }

    /* Set scroll height */
    section.style.height   = (SCROLL_MULT * 100) + 'vh';
    section.style.position = 'relative';

    /* Find or create sticky wrapper */
    var sticky = section.querySelector('.hero-sticky');
    if (!sticky) {
      sticky = document.createElement('div');
      sticky.className = 'hero-sticky';
      var kids = Array.from(section.childNodes);
      kids.forEach(function(k){ sticky.appendChild(k); });
      section.appendChild(sticky);
    }

    /* Force correct sticky styles — critical for mobile */
    sticky.setAttribute('style', [
      'position:sticky',
      'top:0',
      'left:0',
      'width:100%',
      'height:100vh',
      'overflow:hidden',
      'display:flex',
      'align-items:center',
      'justify-content:flex-start',
    ].join(';'));

    /* Remove old canvas */
    var old = document.getElementById('hero-frame-canvas');
    if (old) old.remove();

    /* Create canvas */
    var canvas = document.createElement('canvas');
    canvas.id = 'hero-frame-canvas';
    canvas.setAttribute('style', [
      'position:absolute',
      'top:0',
      'left:0',
      'width:100%',
      'height:100%',
      'z-index:0',
      'display:block',
      'pointer-events:none',
    ].join(';'));
    sticky.insertBefore(canvas, sticky.firstChild);

    /* Lift content above canvas */
    sticky.querySelectorAll('.hero-content,h1,h2,h3,p,a,button,.hero-eyebrow,.hero-headline,.hero-tagline,.hero-cta,.scroll-hint').forEach(function(el){
      el.style.position = 'relative';
      el.style.zIndex   = '2';
    });

    /* Three.js renderer */
    var W = window.innerWidth;
    var H = window.innerHeight;

    var renderer = new THREE.WebGLRenderer({
      canvas: canvas,
      antialias: false,
      alpha: false,
      powerPreference: 'low-power',
    });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(W, H, false);
    renderer.setClearColor(new THREE.Color(PAL.bg), 1);

    var scene  = new THREE.Scene();
    var camera = new THREE.PerspectiveCamera(60, W/H, 0.1, 100);
    camera.position.set(0, 0, 5);

    /* Background gradient plane */
    var bgMat = new THREE.ShaderMaterial({
      uniforms: {
        uP:  { value: 0 },
        uT:  { value: 0 },
        uC1: { value: new THREE.Color(PAL.bg) },
        uC2: { value: new THREE.Color(PAL.a)  },
        uC3: { value: new THREE.Color(PAL.b)  },
      },
      vertexShader: 'varying vec2 v;void main(){v=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}',
      fragmentShader: [
        'uniform float uP,uT;uniform vec3 uC1,uC2,uC3;varying vec2 v;',
        'void main(){',
        '  float t=v.x*0.4+v.y*0.4+sin(uT*0.2+v.x*3.14)*0.05+uP*0.3;',
        '  t=clamp(t,0.,1.);',
        '  vec3 c=mix(uC1,mix(uC2*0.3,uC3*0.2,v.x),t);',
        '  float vig=1.-length(v-0.5)*1.4;',
        '  c*=clamp(vig,0.15,1.);',
        '  gl_FragColor=vec4(c,1.);',
        '}',
      ].join(''),
      depthWrite: false,
      depthTest:  false,
    });
    var bgMesh = new THREE.Mesh(new THREE.PlaneGeometry(20,20), bgMat);
    bgMesh.position.z = -8;
    scene.add(bgMesh);

    /* Particles */
    var isMobile = W < 768;
    var COUNT    = isMobile ? 800 : 1800;

    var pos    = new Float32Array(COUNT * 3);
    var colBuf = new Float32Array(COUNT * 3);
    var phases = new Float32Array(COUNT);
    var szBuf  = new Float32Array(COUNT);

    var c1 = new THREE.Color(PAL.a);
    var c2 = new THREE.Color(PAL.b);
    var cw = new THREE.Color(1,1,1);

    for (var i = 0; i < COUNT; i++) {
      var i3 = i * 3;
      var theta = Math.random() * Math.PI * 2;
      var phi   = Math.acos(2 * Math.random() - 1);
      var r     = 1.0 + Math.random() * 3.5;
      pos[i3]   = r * Math.sin(phi) * Math.cos(theta);
      pos[i3+1] = r * Math.sin(phi) * Math.sin(theta);
      pos[i3+2] = r * Math.cos(phi);
      var mix = Math.random();
      var col = c1.clone().lerp(c2, mix).lerp(cw, mix * 0.25);
      colBuf[i3]=col.r; colBuf[i3+1]=col.g; colBuf[i3+2]=col.b;
      phases[i] = Math.random() * Math.PI * 2;
      szBuf[i]  = 0.005 + Math.random() * 0.012;
    }

    var geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    geo.setAttribute('color',    new THREE.BufferAttribute(colBuf, 3));
    geo.setAttribute('aPhase',   new THREE.BufferAttribute(phases, 1));
    geo.setAttribute('aSize',    new THREE.BufferAttribute(szBuf, 1));

    var mat = new THREE.ShaderMaterial({
      uniforms: {
        uT:  { value: 0 },
        uP:  { value: 0 },
        uPR: { value: renderer.getPixelRatio() },
      },
      vertexShader: [
        'attribute float aPhase,aSize;attribute vec3 color;',
        'varying vec3 vC;varying float vA;',
        'uniform float uT,uP,uPR;',
        'void main(){',
        '  vC=color;',
        '  vec3 p=position;',
        '  float m=sin(uP*3.14159);',
        '  p.x+=sin(aPhase+uT*0.4)*m*0.4;',
        '  p.y+=cos(aPhase+uT*0.3)*m*0.3;',
        '  p.z+=sin(aPhase*1.3+uT*0.5)*m*0.25;',
        '  p.y+=sin(uT*0.5+aPhase)*0.04;',
        '  float a=uP*1.2;float ca=cos(a),sa=sin(a);',
        '  float nx=p.x*ca-p.z*sa;float nz=p.x*sa+p.z*ca;',
        '  p.x=nx;p.z=nz;',
        '  vec4 mv=modelViewMatrix*vec4(p,1.);',
        '  gl_PointSize=aSize*uPR*(350./-mv.z);',
        '  gl_Position=projectionMatrix*mv;',
        '  vA=clamp(1.-(-mv.z-1.)/8.,0.,1.);',
        '}',
      ].join(''),
      fragmentShader: [
        'varying vec3 vC;varying float vA;',
        'void main(){',
        '  float d=length(gl_PointCoord-0.5);',
        '  if(d>0.5)discard;',
        '  float a=1.-smoothstep(0.,0.5,d);',
        '  a=pow(a,1.4);',
        '  gl_FragColor=vec4(vC,a*vA*0.9);',
        '}',
      ].join(''),
      transparent: true,
      depthWrite:  false,
      blending:    THREE.AdditiveBlending,
      vertexColors: true,
    });

    var particles = new THREE.Points(geo, mat);
    scene.add(particles);

    /* Scroll progress — works on mobile touch AND desktop */
    var curP = 0, tgtP = 0;

    function getP() {
      var rect  = section.getBoundingClientRect();
      var total = section.offsetHeight - window.innerHeight;
      if (total <= 0) return 0;
      return Math.max(0, Math.min(1, -rect.top / total));
    }

    function onScroll() { tgtP = getP(); }
    window.addEventListener('scroll',    onScroll, { passive: true });
    window.addEventListener('touchmove', onScroll, { passive: true });
    window.addEventListener('touchend',  onScroll, { passive: true });

    /* Mouse parallax (desktop only) */
    var mx = 0, my = 0;
    window.addEventListener('mousemove', function(e){
      mx = (e.clientX/window.innerWidth  - 0.5) * 2;
      my = -(e.clientY/window.innerHeight - 0.5) * 2;
    }, { passive: true });

    /* Resize */
    window.addEventListener('resize', function(){
      W = window.innerWidth; H = window.innerHeight;
      camera.aspect = W/H;
      camera.updateProjectionMatrix();
      renderer.setSize(W, H, false);
    });

    /* Render loop */
    var t = 0, raf = null;
    function tick() {
      raf = requestAnimationFrame(tick);
      t += 0.01;
      curP += (tgtP - curP) * 0.06;

      mat.uniforms.uT.value  = t;
      mat.uniforms.uP.value  = curP;
      bgMat.uniforms.uT.value = t;
      bgMat.uniforms.uP.value = curP;

      camera.position.x += (mx * 0.4 - camera.position.x) * 0.04;
      camera.position.y += (my * 0.25 - camera.position.y) * 0.04;
      camera.lookAt(0,0,0);

      particles.rotation.y = t * 0.03 + curP * 0.8;
      particles.rotation.x = Math.sin(t * 0.02) * 0.08 + curP * 0.1;

      renderer.render(scene, camera);
    }

    /* Pause when off-screen to save battery */
    if (typeof IntersectionObserver !== 'undefined') {
      new IntersectionObserver(function(entries){
        if (entries[0].isIntersecting) { if (!raf) tick(); }
        else { cancelAnimationFrame(raf); raf = null; }
      }, { threshold: 0 }).observe(section);
    } else {
      tick();
    }

    console.log('[HeroFrame v2] niche='+NICHE+' particles='+COUNT+' mobile='+isMobile);
  }

  /* Bootstrap: run after DOM ready */
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function(){ waitForThree(init); });
  } else {
    waitForThree(init);
  }
})();
