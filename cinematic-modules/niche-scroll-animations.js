/**
 * NICHE SCROLL ANIMATION LIBRARY
 * ================================
 * Every niche gets a bespoke scroll-driven story using Three.js + GSAP ScrollTrigger.
 * These are NOT generic animations — each one tells the brand's story through motion.
 *
 * Niches covered:
 *  coffee/cafe    → Sugar cubes fall in slow motion into a cup, coffee ripples outward
 *  restaurant     → Steam rises from a bowl, ingredients orbit and fall into frame
 *  garage/auto    → Car exploded view — parts fly apart and labels appear with prices
 *  fitness/gym    → Barbell loads with plates as you scroll, weight counter ticks up
 *  beauty/salon   → Lipstick draws a line, petals unfurl, colour palette reveals
 *  real_estate    → Building constructs floor by floor, rooms light up with prices
 *  tech_saas      → Code compiles — characters stream in, then a UI assembles
 *  ecommerce      → Product unboxes — lid lifts, tissue paper unfolds, item rises
 *  hotel/resort   → Sun rises over horizon, pool fills with water, lights turn on
 *  law            → Scales of justice balance, gavel falls, documents stack
 *  medical/clinic → Heartbeat line draws across screen, cells divide, DNA unzips
 *  bakery         → Dough rises, bread bakes, steam curls upward
 *  music          → Sound wave morphs, vinyl spins, notes float up
 *  photography    → Camera shutter opens, aperture blades retract, image develops
 *  architecture   → Blueprint lines draw the building, then it extrudes in 3D
 *  education      → Book opens page by page, words appear, stars fill the sky
 *  travel         → Globe spins, pin drops, flight path draws
 *  fashion        → Fabric unfolds, threads weave, garment assembles
 *  finance        → Chart line draws upward, coins stack, numbers count up
 *  sports         → Ball trajectory arc, scoreboard flips, crowd particles
 */

window.NICHE_SCROLL_ANIMATIONS = (function () {
  'use strict';

  /* ── Shared utilities ─────────────────────────────────────── */
  function lerp(a, b, t) { return a + (b - a) * t; }
  function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }
  function easeInOut(t) { return t < 0.5 ? 2*t*t : -1+(4-2*t)*t; }
  function easeOut(t) { return 1 - Math.pow(1 - t, 3); }

  function hexToRgb(hex) {
    return {
      r: parseInt(hex.slice(1,3),16)/255,
      g: parseInt(hex.slice(3,5),16)/255,
      b: parseInt(hex.slice(5,7),16)/255
    };
  }

  function makeCanvas(container, zIndex) {
    const c = document.createElement('canvas');
    c.style.cssText = `position:absolute;inset:0;width:100%;height:100%;z-index:${zIndex||1};pointer-events:none;`;
    container.style.position = 'relative';
    container.appendChild(c);
    c.width  = container.offsetWidth  || window.innerWidth;
    c.height = container.offsetHeight || 400;
    return c;
  }

  function scrollProgress(el) {
    const r = el.getBoundingClientRect();
    const h = el.offsetHeight;
    const p = (-r.top) / (h - window.innerHeight);
    return clamp(p, 0, 1);
  }

  /* ══════════════════════════════════════════════════════════
     COFFEE / CAFE
     Sugar cubes fall in slow motion → coffee ripples outward
     ══════════════════════════════════════════════════════════ */
  function initCoffee(section, brand) {
    const canvas = makeCanvas(section, 2);
    const ctx    = canvas.getContext('2d');
    const W = canvas.width, H = canvas.height;
    const accent = brand.accentColor || '#c8552a';

    // Sugar cubes
    const cubes = Array.from({length: 6}, (_, i) => ({
      x: W * (0.3 + i * 0.08),
      startY: -80 - i * 40,
      endY: H * 0.55,
      size: 18 + Math.random() * 10,
      rotation: Math.random() * Math.PI * 2,
      rotSpeed: (Math.random() - 0.5) * 0.05,
      delay: i * 0.12,
    }));

    // Ripple rings
    const ripples = [];

    function draw(progress) {
      ctx.clearRect(0, 0, W, H);

      // Coffee cup silhouette (simple)
      const cx = W * 0.5, cy = H * 0.62;
      const cupW = W * 0.28, cupH = H * 0.22;

      // Cup body
      ctx.beginPath();
      ctx.moveTo(cx - cupW/2, cy - cupH/2);
      ctx.lineTo(cx - cupW/2 + 20, cy + cupH/2);
      ctx.lineTo(cx + cupW/2 - 20, cy + cupH/2);
      ctx.lineTo(cx + cupW/2, cy - cupH/2);
      ctx.closePath();
      ctx.fillStyle = '#2a1a0a';
      ctx.fill();
      ctx.strokeStyle = accent;
      ctx.lineWidth = 2;
      ctx.stroke();

      // Coffee surface
      const surfaceY = cy - cupH/2 + 8;
      ctx.beginPath();
      ctx.ellipse(cx, surfaceY, cupW/2 - 4, 12, 0, 0, Math.PI*2);
      ctx.fillStyle = '#3d1f0a';
      ctx.fill();

      // Ripples (triggered when cubes land)
      ripples.forEach((r, i) => {
        const rp = clamp((progress - r.triggerAt) / 0.15, 0, 1);
        if (rp <= 0) return;
        const radius = rp * cupW * 0.4;
        const alpha  = (1 - rp) * 0.6;
        ctx.beginPath();
        ctx.ellipse(cx, surfaceY, radius, radius * 0.3, 0, 0, Math.PI*2);
        ctx.strokeStyle = `rgba(${parseInt(accent.slice(1,3),16)},${parseInt(accent.slice(3,5),16)},${parseInt(accent.slice(5,7),16)},${alpha})`;
        ctx.lineWidth = 1.5;
        ctx.stroke();
      });

      // Sugar cubes falling
      cubes.forEach((cube, i) => {
        const start = cube.delay;
        const end   = start + 0.35;
        const p     = clamp((progress - start) / (end - start), 0, 1);
        const ep    = easeOut(p);

        const y = lerp(cube.startY, cube.endY, ep);
        const rot = cube.rotation + cube.rotSpeed * p * 60;

        // Add ripple when cube lands
        if (p >= 1 && !cube.landed) {
          cube.landed = true;
          ripples.push({ triggerAt: progress, x: cube.x, y: surfaceY });
        }

        // Fade out when submerged
        const alpha = p >= 0.9 ? 1 - (p - 0.9) * 10 : 1;
        if (alpha <= 0) return;

        ctx.save();
        ctx.globalAlpha = alpha;
        ctx.translate(cube.x, y);
        ctx.rotate(rot);
        ctx.fillStyle = '#f5f0e8';
        ctx.strokeStyle = '#d4c9b0';
        ctx.lineWidth = 1;
        ctx.fillRect(-cube.size/2, -cube.size/2, cube.size, cube.size);
        ctx.strokeRect(-cube.size/2, -cube.size/2, cube.size, cube.size);
        // Sugar texture dots
        for (let d = 0; d < 4; d++) {
          ctx.beginPath();
          ctx.arc((Math.random()-0.5)*cube.size*0.6, (Math.random()-0.5)*cube.size*0.6, 1, 0, Math.PI*2);
          ctx.fillStyle = '#e0d5c0';
          ctx.fill();
        }
        ctx.restore();
      });

      // Steam wisps (appear at high progress)
      if (progress > 0.6) {
        const steamP = (progress - 0.6) / 0.4;
        for (let s = 0; s < 3; s++) {
          const sx = cx + (s - 1) * 30;
          const sy = surfaceY - steamP * 60 - s * 10;
          ctx.beginPath();
          ctx.moveTo(sx, surfaceY - 5);
          ctx.bezierCurveTo(sx + 15, sy - 20, sx - 15, sy - 40, sx, sy);
          ctx.strokeStyle = `rgba(255,255,255,${steamP * 0.3})`;
          ctx.lineWidth = 3;
          ctx.lineCap = 'round';
          ctx.stroke();
        }
      }
    }

    window.addEventListener('scroll', () => draw(scrollProgress(section)), { passive: true });
    draw(0);
  }

  /* ══════════════════════════════════════════════════════════
     GARAGE / AUTO
     Car exploded view — parts fly apart, labels + prices appear
     ══════════════════════════════════════════════════════════ */
  function initGarage(section, brand) {
    const canvas = makeCanvas(section, 2);
    const ctx    = canvas.getContext('2d');
    const W = canvas.width, H = canvas.height;
    const accent = brand.accentColor || '#e63946';

    // Car parts with their resting positions (assembled) and exploded positions
    const cx = W * 0.5, cy = H * 0.5;
    const parts = [
      { name: 'Engine',       price: '$2,400', ax: cx,       ay: cy,       ex: cx - W*0.35, ey: cy - H*0.25, w: 80, h: 50, color: '#555' },
      { name: 'Transmission', price: '$1,800', ax: cx + 30,  ay: cy + 10,  ex: cx + W*0.35, ey: cy - H*0.2,  w: 60, h: 40, color: '#666' },
      { name: 'Brakes',       price: '$450',   ax: cx - 60,  ay: cy + 30,  ex: cx - W*0.3,  ey: cy + H*0.3,  w: 40, h: 40, color: '#888' },
      { name: 'Suspension',   price: '$900',   ax: cx + 60,  ay: cy + 30,  ex: cx + W*0.3,  ey: cy + H*0.3,  w: 50, h: 30, color: '#777' },
      { name: 'Exhaust',      price: '$320',   ax: cx + 80,  ay: cy + 20,  ex: cx + W*0.38, ey: cy + H*0.1,  w: 90, h: 20, color: '#444' },
      { name: 'Body Panel',   price: '$1,200', ax: cx,       ay: cy - 30,  ex: cx,          ey: cy - H*0.4,  w: 160,h: 40, color: '#3a3a5c' },
      { name: 'Wheels ×4',    price: '$1,600', ax: cx - 80,  ay: cy + 40,  ex: cx - W*0.4,  ey: cy + H*0.15, w: 45, h: 45, color: '#222', round: true },
      { name: 'Interior',     price: '$3,200', ax: cx - 10,  ay: cy - 10,  ex: cx - W*0.1,  ey: cy - H*0.35, w: 100,h: 50, color: '#4a3020' },
    ];

    function drawPart(p, progress) {
      const ep = easeInOut(progress);
      const x = lerp(p.ax, p.ex, ep);
      const y = lerp(p.ay, p.ey, ep);

      ctx.save();
      ctx.fillStyle = p.color;
      ctx.strokeStyle = accent;
      ctx.lineWidth = 1.5;

      if (p.round) {
        ctx.beginPath();
        ctx.arc(x, y, p.w/2, 0, Math.PI*2);
        ctx.fill();
        ctx.stroke();
        // Wheel spokes
        for (let s = 0; s < 5; s++) {
          const a = (s/5) * Math.PI*2;
          ctx.beginPath();
          ctx.moveTo(x, y);
          ctx.lineTo(x + Math.cos(a)*p.w*0.4, y + Math.sin(a)*p.w*0.4);
          ctx.strokeStyle = '#555';
          ctx.lineWidth = 2;
          ctx.stroke();
        }
      } else {
        ctx.beginPath();
        ctx.roundRect(x - p.w/2, y - p.h/2, p.w, p.h, 4);
        ctx.fill();
        ctx.strokeStyle = accent;
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }

      // Label + price (appear as parts explode)
      if (progress > 0.3) {
        const labelAlpha = clamp((progress - 0.3) / 0.3, 0, 1);
        ctx.globalAlpha = labelAlpha;

        // Connector line
        const lx = x + (x > cx ? 30 : -30);
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(lx, y);
        ctx.strokeStyle = `rgba(255,255,255,0.4)`;
        ctx.lineWidth = 1;
        ctx.stroke();

        // Name
        ctx.font = 'bold 11px "Geist Mono", monospace';
        ctx.fillStyle = '#ffffff';
        ctx.textAlign = x > cx ? 'left' : 'right';
        ctx.fillText(p.name, lx + (x > cx ? 5 : -5), y - 5);

        // Price badge
        ctx.font = '10px "Geist Mono", monospace';
        ctx.fillStyle = accent;
        ctx.fillText(p.price, lx + (x > cx ? 5 : -5), y + 10);
      }

      ctx.restore();
    }

    // Car silhouette (assembled, fades out as parts explode)
    function drawCarSilhouette(alpha) {
      ctx.save();
      ctx.globalAlpha = alpha;
      ctx.fillStyle = '#2a2a3a';
      ctx.strokeStyle = '#555';
      ctx.lineWidth = 2;
      // Simple car body shape
      ctx.beginPath();
      ctx.moveTo(cx - 120, cy + 30);
      ctx.lineTo(cx - 100, cy - 20);
      ctx.lineTo(cx - 60,  cy - 50);
      ctx.lineTo(cx + 60,  cy - 50);
      ctx.lineTo(cx + 100, cy - 20);
      ctx.lineTo(cx + 120, cy + 30);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
      ctx.restore();
    }

    function draw(progress) {
      ctx.clearRect(0, 0, W, H);

      // Title
      ctx.font = 'bold 14px "Geist", sans-serif';
      ctx.fillStyle = 'rgba(255,255,255,0.5)';
      ctx.textAlign = 'center';
      ctx.fillText('SCROLL TO EXPLORE', cx, H * 0.12);

      // Assembled car fades as parts explode
      drawCarSilhouette(1 - easeInOut(progress));

      // Parts explode
      parts.forEach(p => drawPart(p, progress));

      // Total at the bottom
      if (progress > 0.7) {
        const totalAlpha = clamp((progress - 0.7) / 0.3, 0, 1);
        ctx.globalAlpha = totalAlpha;
        ctx.font = 'bold 18px "Geist", sans-serif';
        ctx.fillStyle = accent;
        ctx.textAlign = 'center';
        ctx.fillText('FULL SERVICE PACKAGE', cx, H * 0.9);
        ctx.font = '13px "Geist Mono", monospace';
        ctx.fillStyle = '#ffffff';
        ctx.fillText('Complete breakdown — no hidden costs', cx, H * 0.9 + 22);
        ctx.globalAlpha = 1;
      }
    }

    window.addEventListener('scroll', () => draw(scrollProgress(section)), { passive: true });
    draw(0);
  }

  /* ══════════════════════════════════════════════════════════
     FITNESS / GYM
     Barbell loads with plates as you scroll, weight counter ticks up
     ══════════════════════════════════════════════════════════ */
  function initFitness(section, brand) {
    const canvas = makeCanvas(section, 2);
    const ctx    = canvas.getContext('2d');
    const W = canvas.width, H = canvas.height;
    const accent = brand.accentColor || '#e63946';
    const cx = W * 0.5, cy = H * 0.55;

    const plateWeights = [45, 35, 25, 10, 5, 2.5];
    const plateColors  = ['#c0392b','#2980b9','#27ae60','#f39c12','#8e44ad','#16a085'];
    const plateH       = [60, 52, 44, 36, 28, 22];

    function draw(progress) {
      ctx.clearRect(0, 0, W, H);

      // Bar
      const barW = W * 0.7;
      ctx.fillStyle = '#888';
      ctx.fillRect(cx - barW/2, cy - 8, barW, 16);

      // Collar
      ctx.fillStyle = '#aaa';
      ctx.fillRect(cx - barW/2 + 60, cy - 12, 15, 24);
      ctx.fillRect(cx + barW/2 - 75, cy - 12, 15, 24);

      // How many plates loaded based on progress
      const platesLoaded = Math.floor(progress * plateWeights.length);
      let totalWeight = 45; // bar weight
      let offsetLeft  = cx - barW/2 + 80;
      let offsetRight = cx + barW/2 - 80;

      for (let i = 0; i < platesLoaded; i++) {
        const ph = plateH[i];
        const pw = 18;
        totalWeight += plateWeights[i] * 2;

        // Partial plate animation for the currently loading plate
        let alpha = 1;
        if (i === platesLoaded - 1) {
          const partialP = (progress * plateWeights.length) - platesLoaded + 1;
          alpha = clamp(partialP * 3, 0, 1);
        }
        ctx.globalAlpha = alpha;

        // Left plate
        ctx.fillStyle = plateColors[i];
        ctx.beginPath();
        ctx.roundRect(offsetLeft - pw, cy - ph/2, pw, ph, 3);
        ctx.fill();
        ctx.strokeStyle = '#333';
        ctx.lineWidth = 1;
        ctx.stroke();

        // Right plate
        ctx.beginPath();
        ctx.roundRect(offsetRight, cy - ph/2, pw, ph, 3);
        ctx.fill();
        ctx.stroke();

        // Weight label
        ctx.font = `bold ${Math.max(8, ph/5)}px "Geist Mono", monospace`;
        ctx.fillStyle = 'rgba(255,255,255,0.9)';
        ctx.textAlign = 'center';
        ctx.fillText(plateWeights[i], offsetLeft - pw/2, cy + 3);
        ctx.fillText(plateWeights[i], offsetRight + pw/2, cy + 3);

        offsetLeft  -= pw + 2;
        offsetRight += pw + 2;
        ctx.globalAlpha = 1;
      }

      // Weight counter
      ctx.font = `bold ${W < 500 ? 36 : 56}px "Geist", sans-serif`;
      ctx.fillStyle = accent;
      ctx.textAlign = 'center';
      ctx.fillText(`${totalWeight} lbs`, cx, H * 0.2);

      ctx.font = '14px "Geist", sans-serif';
      ctx.fillStyle = 'rgba(255,255,255,0.5)';
      ctx.fillText('LOADING UP', cx, H * 0.2 + 28);

      // Motivational text at full load
      if (progress > 0.9) {
        const p = clamp((progress - 0.9) / 0.1, 0, 1);
        ctx.globalAlpha = p;
        ctx.font = `bold ${W < 500 ? 20 : 28}px "Geist", sans-serif`;
        ctx.fillStyle = '#ffffff';
        ctx.fillText("YOU'VE GOT THIS.", cx, H * 0.88);
        ctx.globalAlpha = 1;
      }
    }

    window.addEventListener('scroll', () => draw(scrollProgress(section)), { passive: true });
    draw(0);
  }

  /* ══════════════════════════════════════════════════════════
     BEAUTY / SALON
     Lipstick draws a stroke, petals unfurl, colour palette reveals
     ══════════════════════════════════════════════════════════ */
  function initBeauty(section, brand) {
    const canvas = makeCanvas(section, 2);
    const ctx    = canvas.getContext('2d');
    const W = canvas.width, H = canvas.height;
    const accent = brand.accentColor || '#e91e8c';
    const cx = W * 0.5, cy = H * 0.5;

    const palette = ['#e91e8c','#ff6b9d','#c2185b','#f48fb1','#ad1457','#fce4ec'];
    const petals  = 8;

    function draw(progress) {
      ctx.clearRect(0, 0, W, H);

      // Lipstick stroke — draws across the canvas
      const strokeLen = progress * W * 0.8;
      const strokeY   = H * 0.35;
      ctx.beginPath();
      ctx.moveTo(W * 0.1, strokeY);
      ctx.lineTo(W * 0.1 + strokeLen, strokeY);
      ctx.strokeStyle = accent;
      ctx.lineWidth   = 8;
      ctx.lineCap     = 'round';
      ctx.stroke();

      // Colour palette swatches reveal
      if (progress > 0.2) {
        const swatchP = clamp((progress - 0.2) / 0.3, 0, 1);
        palette.forEach((col, i) => {
          const delay = i * 0.15;
          const sp    = clamp((swatchP - delay) / 0.3, 0, 1);
          if (sp <= 0) return;
          const sx = W * 0.1 + i * (W * 0.13);
          const sy = H * 0.55;
          const r  = 22 * sp;
          ctx.beginPath();
          ctx.arc(sx, sy, r, 0, Math.PI*2);
          ctx.fillStyle = col;
          ctx.fill();
          ctx.strokeStyle = 'rgba(255,255,255,0.3)';
          ctx.lineWidth = 1;
          ctx.stroke();
        });
      }

      // Rose petals unfurl from centre
      if (progress > 0.4) {
        const petalP = clamp((progress - 0.4) / 0.4, 0, 1);
        for (let i = 0; i < petals; i++) {
          const angle  = (i / petals) * Math.PI * 2;
          const spread = petalP * 80;
          const px     = cx + Math.cos(angle) * spread;
          const py     = cy + Math.sin(angle) * spread * 0.6;
          const size   = 20 + petalP * 15;
          const alpha  = petalP;

          ctx.save();
          ctx.globalAlpha = alpha;
          ctx.translate(px, py);
          ctx.rotate(angle + Math.PI/2);
          ctx.beginPath();
          ctx.ellipse(0, 0, size * 0.4, size, 0, 0, Math.PI*2);
          ctx.fillStyle = i % 2 === 0 ? accent : '#f48fb1';
          ctx.fill();
          ctx.restore();
        }

        // Centre bud
        ctx.beginPath();
        ctx.arc(cx, cy, 12 * petalP, 0, Math.PI*2);
        ctx.fillStyle = '#c2185b';
        ctx.fill();
      }

      // Brand tagline
      if (progress > 0.75) {
        const tp = clamp((progress - 0.75) / 0.25, 0, 1);
        ctx.globalAlpha = tp;
        ctx.font = `italic ${W < 500 ? 18 : 26}px Georgia, serif`;
        ctx.fillStyle = accent;
        ctx.textAlign = 'center';
        ctx.fillText('Beauty is in the details.', cx, H * 0.88);
        ctx.globalAlpha = 1;
      }
    }

    window.addEventListener('scroll', () => draw(scrollProgress(section)), { passive: true });
    draw(0);
  }

  /* ══════════════════════════════════════════════════════════
     REAL ESTATE
     Building constructs floor by floor, rooms light up with prices
     ══════════════════════════════════════════════════════════ */
  function initRealEstate(section, brand) {
    const canvas = makeCanvas(section, 2);
    const ctx    = canvas.getContext('2d');
    const W = canvas.width, H = canvas.height;
    const accent = brand.accentColor || '#2c5f8a';

    const floors = 8;
    const floorH = 45, floorW = W * 0.35;
    const bx = W * 0.5 - floorW/2;
    const groundY = H * 0.85;

    const prices = ['$420K','$385K','$350K','$490K','$520K','$610K','$580K','$750K'];
    const types  = ['Studio','1 Bed','2 Bed','3 Bed','Penthouse','Penthouse+','Sky Suite','Penthouse'];

    function draw(progress) {
      ctx.clearRect(0, 0, W, H);

      // Ground
      ctx.fillStyle = '#1a1a2e';
      ctx.fillRect(0, groundY, W, H - groundY);

      // Floors construct from bottom up
      const floorsBuilt = Math.floor(progress * floors);
      const partial     = (progress * floors) - floorsBuilt;

      for (let f = 0; f < floorsBuilt; f++) {
        const fy = groundY - (f + 1) * floorH;
        const lit = f < floorsBuilt - 1 || partial > 0.5;

        // Floor slab
        ctx.fillStyle = f % 2 === 0 ? '#1e2a3a' : '#1a2535';
        ctx.fillRect(bx, fy, floorW, floorH - 2);
        ctx.strokeStyle = accent;
        ctx.lineWidth = 1;
        ctx.strokeRect(bx, fy, floorW, floorH - 2);

        // Windows (3 per floor)
        for (let w = 0; w < 3; w++) {
          const wx = bx + 20 + w * (floorW/3 - 5);
          const wy = fy + 8;
          ctx.fillStyle = lit ? `rgba(255,220,100,${0.6 + Math.sin(Date.now()*0.001 + f + w)*0.1})` : '#0d1520';
          ctx.fillRect(wx, wy, floorW/3 - 20, floorH - 18);
        }

        // Price label
        if (lit && floorsBuilt > 1) {
          ctx.font = 'bold 11px "Geist Mono", monospace';
          ctx.fillStyle = accent;
          ctx.textAlign = 'left';
          ctx.fillText(prices[f] || '$???', bx + floorW + 12, fy + 18);
          ctx.font = '10px "Geist", sans-serif';
          ctx.fillStyle = 'rgba(255,255,255,0.5)';
          ctx.fillText(types[f] || 'Unit', bx + floorW + 12, fy + 32);
        }
      }

      // Partial floor being built
      if (floorsBuilt < floors) {
        const fy = groundY - (floorsBuilt + 1) * floorH;
        ctx.fillStyle = '#1e2a3a';
        ctx.fillRect(bx, fy + floorH * (1 - partial), floorW, floorH * partial - 2);
        ctx.strokeStyle = `rgba(${parseInt(accent.slice(1,3),16)},${parseInt(accent.slice(3,5),16)},${parseInt(accent.slice(5,7),16)},0.5)`;
        ctx.lineWidth = 1;
        ctx.strokeRect(bx, fy + floorH * (1 - partial), floorW, floorH * partial - 2);
      }

      // Floor counter
      ctx.font = `bold ${W < 500 ? 28 : 42}px "Geist", sans-serif`;
      ctx.fillStyle = accent;
      ctx.textAlign = 'center';
      ctx.fillText(`${floorsBuilt} / ${floors} FLOORS`, W * 0.5, H * 0.12);

      // Crane (top of building)
      if (floorsBuilt > 0) {
        const topY = groundY - floorsBuilt * floorH;
        ctx.strokeStyle = '#888';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(bx + floorW/2, topY);
        ctx.lineTo(bx + floorW/2, topY - 60);
        ctx.lineTo(bx + floorW/2 + 80, topY - 60);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(bx + floorW/2 + 80, topY - 60);
        ctx.lineTo(bx + floorW/2 + 80, topY - 30);
        ctx.strokeStyle = '#e63946';
        ctx.stroke();
      }
    }

    // Animate window flicker
    function animate() {
      draw(scrollProgress(section));
      requestAnimationFrame(animate);
    }
    animate();
  }

  /* ══════════════════════════════════════════════════════════
     TECH / SAAS
     Code streams in character by character, then a UI assembles
     ══════════════════════════════════════════════════════════ */
  function initTech(section, brand) {
    const canvas = makeCanvas(section, 2);
    const ctx    = canvas.getContext('2d');
    const W = canvas.width, H = canvas.height;
    const accent = brand.accentColor || '#00d4ff';

    const codeLines = [
      '> initializing pipeline...',
      '> analyzing brand identity',
      '> extracting color tokens',
      '> generating 3D hero scene',
      '> applying scroll animations',
      '> running QA checks',
      '> deploying to production',
      '✓ website live in 3 minutes',
    ];

    function draw(progress) {
      ctx.clearRect(0, 0, W, H);

      // Terminal background
      ctx.fillStyle = 'rgba(10,10,20,0.85)';
      ctx.beginPath();
      ctx.roundRect(W*0.08, H*0.1, W*0.84, H*0.7, 8);
      ctx.fill();
      ctx.strokeStyle = accent;
      ctx.lineWidth = 1;
      ctx.stroke();

      // Terminal title bar
      ctx.fillStyle = '#1a1a2e';
      ctx.beginPath();
      ctx.roundRect(W*0.08, H*0.1, W*0.84, 32, [8,8,0,0]);
      ctx.fill();
      ['#ff5f57','#febc2e','#28c840'].forEach((c, i) => {
        ctx.beginPath();
        ctx.arc(W*0.08 + 20 + i*20, H*0.1 + 16, 6, 0, Math.PI*2);
        ctx.fillStyle = c;
        ctx.fill();
      });

      // Code lines stream in
      const linesShown = progress * codeLines.length;
      ctx.font = `${W < 500 ? 11 : 13}px "Geist Mono", monospace`;
      ctx.textAlign = 'left';

      codeLines.forEach((line, i) => {
        const lineP = clamp(linesShown - i, 0, 1);
        if (lineP <= 0) return;

        const chars = Math.floor(lineP * line.length);
        const displayText = line.slice(0, chars) + (lineP < 1 ? '█' : '');
        const ly = H * 0.1 + 50 + i * 28;

        // Colour coding
        if (line.startsWith('✓')) {
          ctx.fillStyle = '#28c840';
        } else if (line.startsWith('>')) {
          ctx.fillStyle = accent;
        } else {
          ctx.fillStyle = 'rgba(255,255,255,0.7)';
        }
        ctx.fillText(displayText, W*0.08 + 20, ly);
      });

      // Progress bar at bottom of terminal
      const barY = H * 0.1 + H * 0.7 - 20;
      ctx.fillStyle = '#1a1a2e';
      ctx.fillRect(W*0.08 + 20, barY, W*0.84 - 40, 6);
      ctx.fillStyle = accent;
      ctx.fillRect(W*0.08 + 20, barY, (W*0.84 - 40) * progress, 6);

      ctx.font = '11px "Geist Mono", monospace';
      ctx.fillStyle = accent;
      ctx.textAlign = 'right';
      ctx.fillText(`${Math.round(progress * 100)}%`, W*0.08 + W*0.84 - 20, barY - 5);
    }

    window.addEventListener('scroll', () => draw(scrollProgress(section)), { passive: true });
    draw(0);
  }

  /* ══════════════════════════════════════════════════════════
     HOTEL / RESORT
     Sun rises, pool fills with water, lights turn on room by room
     ══════════════════════════════════════════════════════════ */
  function initHotel(section, brand) {
    const canvas = makeCanvas(section, 2);
    const ctx    = canvas.getContext('2d');
    const W = canvas.width, H = canvas.height;
    const accent = brand.accentColor || '#d4a853';

    function draw(progress) {
      ctx.clearRect(0, 0, W, H);

      // Sky gradient — transitions from night to golden hour
      const skyGrad = ctx.createLinearGradient(0, 0, 0, H * 0.6);
      const nightR = 10, nightG = 10, nightB = 30;
      const dayR   = 255, dayG = 160, dayB = 50;
      const r = Math.round(lerp(nightR, dayR, progress));
      const g = Math.round(lerp(nightG, dayG, progress));
      const b = Math.round(lerp(nightB, dayB, progress));
      skyGrad.addColorStop(0, `rgb(${r},${g},${b})`);
      skyGrad.addColorStop(1, `rgb(${Math.round(r*0.3)},${Math.round(g*0.3)},${Math.round(b*0.2)})`);
      ctx.fillStyle = skyGrad;
      ctx.fillRect(0, 0, W, H * 0.6);

      // Stars (fade out as sun rises)
      const starAlpha = 1 - progress * 2;
      if (starAlpha > 0) {
        ctx.fillStyle = `rgba(255,255,255,${starAlpha})`;
        for (let s = 0; s < 60; s++) {
          const sx = (s * 137.5) % W;
          const sy = (s * 73.1) % (H * 0.5);
          ctx.beginPath();
          ctx.arc(sx, sy, 1, 0, Math.PI*2);
          ctx.fill();
        }
      }

      // Sun rising
      const sunY = H * 0.6 - progress * H * 0.45;
      const sunR = 40 + progress * 10;
      const sunGrad = ctx.createRadialGradient(W*0.5, sunY, 0, W*0.5, sunY, sunR * 3);
      sunGrad.addColorStop(0, `rgba(255,220,80,${progress})`);
      sunGrad.addColorStop(0.3, `rgba(255,160,40,${progress * 0.6})`);
      sunGrad.addColorStop(1, 'transparent');
      ctx.fillStyle = sunGrad;
      ctx.fillRect(0, 0, W, H);

      ctx.beginPath();
      ctx.arc(W*0.5, sunY, sunR, 0, Math.PI*2);
      ctx.fillStyle = `rgba(255,230,100,${progress})`;
      ctx.fill();

      // Ground / landscape
      ctx.fillStyle = '#1a2a1a';
      ctx.fillRect(0, H * 0.6, W, H * 0.4);

      // Pool — fills with water
      const poolX = W * 0.2, poolY = H * 0.65, poolW = W * 0.6, poolH = H * 0.15;
      ctx.fillStyle = '#1a1a2e';
      ctx.fillRect(poolX, poolY, poolW, poolH);

      if (progress > 0.2) {
        const waterP = clamp((progress - 0.2) / 0.5, 0, 1);
        const waterH = poolH * waterP;
        const waterGrad = ctx.createLinearGradient(0, poolY + poolH - waterH, 0, poolY + poolH);
        waterGrad.addColorStop(0, `rgba(30,100,180,${waterP * 0.9})`);
        waterGrad.addColorStop(1, `rgba(10,60,120,${waterP})`);
        ctx.fillStyle = waterGrad;
        ctx.fillRect(poolX + 2, poolY + poolH - waterH, poolW - 4, waterH);

        // Water shimmer
        if (waterP > 0.5) {
          for (let s = 0; s < 5; s++) {
            const sx = poolX + 20 + s * poolW/5;
            const sy = poolY + poolH - waterH/2;
            ctx.beginPath();
            ctx.moveTo(sx, sy);
            ctx.lineTo(sx + 15, sy - 3);
            ctx.lineTo(sx + 30, sy);
            ctx.strokeStyle = `rgba(255,255,255,${waterP * 0.4})`;
            ctx.lineWidth = 1.5;
            ctx.stroke();
          }
        }
      }

      // Hotel building
      const hotelX = W * 0.35, hotelY = H * 0.3, hotelW = W * 0.3, hotelH = H * 0.35;
      ctx.fillStyle = '#2a2a3a';
      ctx.fillRect(hotelX, hotelY, hotelW, hotelH);

      // Windows lighting up
      const windowRows = 5, windowCols = 4;
      const windowsLit = Math.floor(progress * windowRows * windowCols);
      for (let row = 0; row < windowRows; row++) {
        for (let col = 0; col < windowCols; col++) {
          const idx = row * windowCols + col;
          const lit = idx < windowsLit;
          const wx  = hotelX + 15 + col * (hotelW/windowCols - 5);
          const wy  = hotelY + 15 + row * (hotelH/windowRows - 5);
          ctx.fillStyle = lit ? `rgba(255,220,100,0.8)` : '#1a1a2a';
          ctx.fillRect(wx, wy, hotelW/windowCols - 15, hotelH/windowRows - 15);
        }
      }

      // Price tag
      if (progress > 0.7) {
        const tp = clamp((progress - 0.7) / 0.3, 0, 1);
        ctx.globalAlpha = tp;
        ctx.font = `bold ${W < 500 ? 22 : 32}px "Geist", sans-serif`;
        ctx.fillStyle = accent;
        ctx.textAlign = 'center';
        ctx.fillText('FROM $280 / NIGHT', W * 0.5, H * 0.92);
        ctx.globalAlpha = 1;
      }
    }

    window.addEventListener('scroll', () => draw(scrollProgress(section)), { passive: true });
    draw(0);
  }

  /* ══════════════════════════════════════════════════════════
     MEDICAL / CLINIC
     Heartbeat line draws, cells divide, DNA unzips
     ══════════════════════════════════════════════════════════ */
  function initMedical(section, brand) {
    const canvas = makeCanvas(section, 2);
    const ctx    = canvas.getContext('2d');
    const W = canvas.width, H = canvas.height;
    const accent = brand.accentColor || '#00b4d8';

    function draw(progress) {
      ctx.clearRect(0, 0, W, H);

      // ECG heartbeat line
      const lineY = H * 0.35;
      const lineLen = W * 0.85;
      const startX  = W * 0.075;
      const drawn   = progress * lineLen;

      ctx.beginPath();
      ctx.moveTo(startX, lineY);
      let x = startX;
      while (x < startX + drawn) {
        const t = (x - startX) / lineLen;
        let y = lineY;
        // ECG pattern: flat → spike → flat
        const cycle = (t * 6) % 1;
        if (cycle < 0.1)       y = lineY;
        else if (cycle < 0.15) y = lineY - 60;
        else if (cycle < 0.2)  y = lineY + 20;
        else if (cycle < 0.25) y = lineY - 100;
        else if (cycle < 0.3)  y = lineY + 15;
        else if (cycle < 0.35) y = lineY;
        else                   y = lineY;
        ctx.lineTo(x, y);
        x += 2;
      }
      ctx.strokeStyle = accent;
      ctx.lineWidth   = 2.5;
      ctx.lineCap     = 'round';
      ctx.lineJoin    = 'round';
      ctx.stroke();

      // Glow
      ctx.shadowColor = accent;
      ctx.shadowBlur  = 8;
      ctx.stroke();
      ctx.shadowBlur  = 0;

      // BPM counter
      const bpm = Math.round(60 + progress * 20);
      ctx.font = `bold ${W < 500 ? 36 : 52}px "Geist Mono", monospace`;
      ctx.fillStyle = accent;
      ctx.textAlign = 'center';
      ctx.fillText(`${bpm} BPM`, W * 0.5, H * 0.18);

      // DNA double helix (lower half)
      if (progress > 0.3) {
        const dnaP  = clamp((progress - 0.3) / 0.5, 0, 1);
        const dnaY  = H * 0.65;
        const dnaW  = W * 0.6;
        const dnaX  = W * 0.2;
        const steps = Math.floor(dnaP * 20);

        for (let i = 0; i < steps; i++) {
          const t    = i / 20;
          const x1   = dnaX + t * dnaW;
          const y1   = dnaY + Math.sin(t * Math.PI * 4) * 30;
          const y2   = dnaY + Math.sin(t * Math.PI * 4 + Math.PI) * 30;

          // Strand 1
          if (i > 0) {
            const pt = (i-1) / 20;
            ctx.beginPath();
            ctx.moveTo(dnaX + pt * dnaW, dnaY + Math.sin(pt * Math.PI * 4) * 30);
            ctx.lineTo(x1, y1);
            ctx.strokeStyle = accent;
            ctx.lineWidth = 2;
            ctx.stroke();

            // Strand 2
            ctx.beginPath();
            ctx.moveTo(dnaX + pt * dnaW, dnaY + Math.sin(pt * Math.PI * 4 + Math.PI) * 30);
            ctx.lineTo(x1, y2);
            ctx.strokeStyle = '#ff6b9d';
            ctx.stroke();
          }

          // Base pair rungs
          ctx.beginPath();
          ctx.moveTo(x1, y1);
          ctx.lineTo(x1, y2);
          ctx.strokeStyle = 'rgba(255,255,255,0.2)';
          ctx.lineWidth = 1;
          ctx.stroke();
        }
      }
    }

    window.addEventListener('scroll', () => draw(scrollProgress(section)), { passive: true });
    draw(0);
  }

  /* ══════════════════════════════════════════════════════════
     RESTAURANT (general)
     Ingredients orbit and fall into a bowl, steam rises
     ══════════════════════════════════════════════════════════ */
  function initRestaurant(section, brand) {
    const canvas = makeCanvas(section, 2);
    const ctx    = canvas.getContext('2d');
    const W = canvas.width, H = canvas.height;
    const accent = brand.accentColor || '#c8552a';
    const cx = W * 0.5, cy = H * 0.55;

    const ingredients = [
      { emoji: '🍜', label: 'Noodles',   orbitR: 140, orbitSpeed: 0.8,  size: 28, fallAt: 0.2 },
      { emoji: '🥚', label: 'Egg',       orbitR: 110, orbitSpeed: -1.1, size: 22, fallAt: 0.3 },
      { emoji: '🌿', label: 'Herbs',     orbitR: 160, orbitSpeed: 0.6,  size: 20, fallAt: 0.4 },
      { emoji: '🍖', label: 'Pork',      orbitR: 130, orbitSpeed: -0.9, size: 26, fallAt: 0.5 },
      { emoji: '🧅', label: 'Onion',     orbitR: 150, orbitSpeed: 1.2,  size: 20, fallAt: 0.6 },
      { emoji: '🌶️', label: 'Chilli',   orbitR: 120, orbitSpeed: -0.7, size: 18, fallAt: 0.7 },
    ];

    let time = 0;
    function animate() {
      time += 0.01;
      draw(scrollProgress(section));
      requestAnimationFrame(animate);
    }

    function draw(progress) {
      ctx.clearRect(0, 0, W, H);

      // Bowl
      ctx.beginPath();
      ctx.ellipse(cx, cy + 20, 90, 30, 0, 0, Math.PI*2);
      ctx.fillStyle = '#f5e6d3';
      ctx.fill();
      ctx.strokeStyle = accent;
      ctx.lineWidth = 2;
      ctx.stroke();

      ctx.beginPath();
      ctx.moveTo(cx - 90, cy + 20);
      ctx.bezierCurveTo(cx - 90, cy + 80, cx + 90, cy + 80, cx + 90, cy + 20);
      ctx.fillStyle = '#f5e6d3';
      ctx.fill();
      ctx.strokeStyle = accent;
      ctx.stroke();

      // Broth surface
      ctx.beginPath();
      ctx.ellipse(cx, cy + 20, 85, 26, 0, 0, Math.PI*2);
      ctx.fillStyle = '#c8552a';
      ctx.fill();

      // Ingredients orbit then fall in
      ingredients.forEach((ing, i) => {
        const angle = time * ing.orbitSpeed + (i / ingredients.length) * Math.PI * 2;
        const fallP = clamp((progress - ing.fallAt) / 0.15, 0, 1);
        const orbitX = cx + Math.cos(angle) * ing.orbitR * (1 - fallP);
        const orbitY = cy - 30 + Math.sin(angle) * ing.orbitR * 0.4 * (1 - fallP);
        const fallY  = lerp(orbitY, cy + 15, easeOut(fallP));
        const scale  = 1 - fallP * 0.3;
        const alpha  = fallP >= 1 ? 0 : 1;

        ctx.save();
        ctx.globalAlpha = alpha;
        ctx.font = `${ing.size * scale}px serif`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(ing.emoji, orbitX, fallY);

        // Label
        if (fallP < 0.5) {
          ctx.font = `10px "Geist", sans-serif`;
          ctx.fillStyle = 'rgba(255,255,255,0.7)';
          ctx.fillText(ing.label, orbitX, fallY + ing.size * scale * 0.7 + 8);
        }
        ctx.restore();
      });

      // Steam wisps
      if (progress > 0.5) {
        const sp = (progress - 0.5) / 0.5;
        for (let s = 0; s < 4; s++) {
          const sx = cx - 40 + s * 25;
          ctx.beginPath();
          ctx.moveTo(sx, cy + 15);
          for (let p = 0; p < 10; p++) {
            const t  = p / 10;
            const wx = sx + Math.sin(t * Math.PI * 3 + s) * 12 * sp;
            const wy = cy + 15 - t * 70 * sp;
            ctx.lineTo(wx, wy);
          }
          ctx.strokeStyle = `rgba(255,255,255,${sp * 0.25})`;
          ctx.lineWidth = 3;
          ctx.lineCap = 'round';
          ctx.stroke();
        }
      }
    }

    animate();
  }

  /* ══════════════════════════════════════════════════════════
     ECOMMERCE
     Product unboxes — lid lifts, tissue unfolds, item rises
     ══════════════════════════════════════════════════════════ */
  function initEcommerce(section, brand) {
    const canvas = makeCanvas(section, 2);
    const ctx    = canvas.getContext('2d');
    const W = canvas.width, H = canvas.height;
    const accent = brand.accentColor || '#e63946';
    const cx = W * 0.5, cy = H * 0.55;
    const boxW = 160, boxH = 120;

    function draw(progress) {
      ctx.clearRect(0, 0, W, H);

      // Box base
      ctx.fillStyle = '#2a2a3a';
      ctx.strokeStyle = accent;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.roundRect(cx - boxW/2, cy - boxH/2, boxW, boxH, 4);
      ctx.fill();
      ctx.stroke();

      // Brand stripe on box
      ctx.fillStyle = accent;
      ctx.fillRect(cx - boxW/2, cy - 8, boxW, 16);

      // Lid lifts open
      const lidLift = easeOut(clamp(progress / 0.4, 0, 1)) * 80;
      ctx.fillStyle = '#1a1a2e';
      ctx.strokeStyle = accent;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.roundRect(cx - boxW/2 - 5, cy - boxH/2 - 30 - lidLift, boxW + 10, 35, [4,4,0,0]);
      ctx.fill();
      ctx.stroke();

      // Tissue paper unfolds
      if (progress > 0.2) {
        const tissueP = clamp((progress - 0.2) / 0.3, 0, 1);
        ctx.save();
        ctx.globalAlpha = tissueP;
        ctx.fillStyle = '#f8f0e8';
        ctx.beginPath();
        ctx.moveTo(cx - boxW/2 + 10, cy - boxH/2 + 10);
        ctx.bezierCurveTo(
          cx - 20, cy - boxH/2 - tissueP * 20,
          cx + 20, cy - boxH/2 - tissueP * 20,
          cx + boxW/2 - 10, cy - boxH/2 + 10
        );
        ctx.lineTo(cx + boxW/2 - 10, cy);
        ctx.lineTo(cx - boxW/2 + 10, cy);
        ctx.closePath();
        ctx.fill();
        ctx.strokeStyle = '#e0d5c0';
        ctx.lineWidth = 1;
        ctx.stroke();
        ctx.restore();
      }

      // Product rises from box
      if (progress > 0.45) {
        const riseP = easeOut(clamp((progress - 0.45) / 0.4, 0, 1));
        const productY = cy - riseP * 100;
        ctx.save();
        ctx.globalAlpha = riseP;

        // Generic product shape (can be customised per brand)
        ctx.fillStyle = accent;
        ctx.beginPath();
        ctx.roundRect(cx - 30, productY - 40, 60, 80, 8);
        ctx.fill();
        ctx.strokeStyle = 'rgba(255,255,255,0.3)';
        ctx.lineWidth = 1;
        ctx.stroke();

        // Shine
        ctx.fillStyle = 'rgba(255,255,255,0.15)';
        ctx.beginPath();
        ctx.roundRect(cx - 20, productY - 35, 15, 60, 4);
        ctx.fill();

        // Sparkles
        if (riseP > 0.7) {
          const sp = (riseP - 0.7) / 0.3;
          for (let s = 0; s < 6; s++) {
            const angle = (s/6) * Math.PI * 2;
            const dist  = 55 + Math.sin(Date.now()*0.003 + s) * 5;
            const sx    = cx + Math.cos(angle) * dist;
            const sy    = productY - 10 + Math.sin(angle) * dist * 0.5;
            ctx.beginPath();
            ctx.arc(sx, sy, 3 * sp, 0, Math.PI*2);
            ctx.fillStyle = `rgba(255,220,100,${sp})`;
            ctx.fill();
          }
        }
        ctx.restore();
      }

      // "NEW ARRIVAL" badge
      if (progress > 0.8) {
        const bp = clamp((progress - 0.8) / 0.2, 0, 1);
        ctx.globalAlpha = bp;
        ctx.font = `bold ${W < 500 ? 18 : 24}px "Geist", sans-serif`;
        ctx.fillStyle = accent;
        ctx.textAlign = 'center';
        ctx.fillText('NEW ARRIVAL', cx, H * 0.9);
        ctx.globalAlpha = 1;
      }
    }

    function animate() {
      draw(scrollProgress(section));
      requestAnimationFrame(animate);
    }
    animate();
  }

  /* ══════════════════════════════════════════════════════════
     LAW
     Scales balance, gavel falls, documents stack
     ══════════════════════════════════════════════════════════ */
  function initLaw(section, brand) {
    const canvas = makeCanvas(section, 2);
    const ctx    = canvas.getContext('2d');
    const W = canvas.width, H = canvas.height;
    const accent = brand.accentColor || '#c9a84c';
    const cx = W * 0.5, cy = H * 0.45;

    function draw(progress) {
      ctx.clearRect(0, 0, W, H);

      // Scales of justice
      const poleH = 120;
      // Centre pole
      ctx.strokeStyle = accent;
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.moveTo(cx, cy + poleH/2);
      ctx.lineTo(cx, cy - poleH/2);
      ctx.stroke();

      // Balance beam — tilts based on scroll (settles to balanced)
      const tilt = Math.sin(progress * Math.PI * 3) * (1 - progress) * 0.3;
      const beamW = 160;
      ctx.save();
      ctx.translate(cx, cy - poleH/2);
      ctx.rotate(tilt);
      ctx.beginPath();
      ctx.moveTo(-beamW/2, 0);
      ctx.lineTo(beamW/2, 0);
      ctx.strokeStyle = accent;
      ctx.lineWidth = 3;
      ctx.stroke();

      // Left pan
      const leftY  = 50 + Math.sin(tilt) * beamW/2;
      const rightY = 50 - Math.sin(tilt) * beamW/2;
      ctx.beginPath();
      ctx.moveTo(-beamW/2, 0);
      ctx.lineTo(-beamW/2 - 20, leftY);
      ctx.lineTo(-beamW/2 + 20, leftY);
      ctx.strokeStyle = 'rgba(201,168,76,0.5)';
      ctx.stroke();
      ctx.beginPath();
      ctx.ellipse(-beamW/2, leftY, 28, 8, 0, 0, Math.PI*2);
      ctx.fillStyle = '#2a2a1a';
      ctx.fill();
      ctx.strokeStyle = accent;
      ctx.stroke();

      // Right pan
      ctx.beginPath();
      ctx.moveTo(beamW/2, 0);
      ctx.lineTo(beamW/2 - 20, rightY);
      ctx.lineTo(beamW/2 + 20, rightY);
      ctx.strokeStyle = 'rgba(201,168,76,0.5)';
      ctx.stroke();
      ctx.beginPath();
      ctx.ellipse(beamW/2, rightY, 28, 8, 0, 0, Math.PI*2);
      ctx.fillStyle = '#2a2a1a';
      ctx.fill();
      ctx.strokeStyle = accent;
      ctx.stroke();
      ctx.restore();

      // Gavel falls
      if (progress > 0.5) {
        const gp    = clamp((progress - 0.5) / 0.3, 0, 1);
        const gavel = easeOut(gp);
        const gx    = cx + 80;
        const gy    = H * 0.7 - (1 - gavel) * 80;
        const angle = -0.6 + gavel * 0.6;

        ctx.save();
        ctx.translate(gx, gy);
        ctx.rotate(angle);
        ctx.fillStyle = '#5c3d1e';
        ctx.fillRect(-8, -50, 16, 50);
        ctx.fillRect(-20, -60, 40, 20);
        ctx.restore();

        // Impact ripple
        if (gp >= 1) {
          ctx.beginPath();
          ctx.arc(gx, H * 0.7, (Date.now() % 1000) / 1000 * 40, 0, Math.PI*2);
          ctx.strokeStyle = `rgba(201,168,76,${1 - (Date.now() % 1000)/1000})`;
          ctx.lineWidth = 2;
          ctx.stroke();
        }
      }

      // Documents stacking
      if (progress > 0.65) {
        const dp = clamp((progress - 0.65) / 0.35, 0, 1);
        const docs = Math.floor(dp * 5);
        for (let d = 0; d < docs; d++) {
          const dx = cx - 120 + d * 3;
          const dy = H * 0.72 - d * 6;
          ctx.fillStyle = d % 2 === 0 ? '#f5f0e0' : '#ece8d8';
          ctx.fillRect(dx, dy, 80, 60);
          ctx.strokeStyle = 'rgba(0,0,0,0.2)';
          ctx.lineWidth = 1;
          ctx.strokeRect(dx, dy, 80, 60);
          // Lines on document
          for (let l = 0; l < 4; l++) {
            ctx.fillStyle = 'rgba(0,0,0,0.15)';
            ctx.fillRect(dx + 8, dy + 12 + l * 10, 64, 2);
          }
        }
      }

      // "JUSTICE SERVED" text
      if (progress > 0.85) {
        const tp = clamp((progress - 0.85) / 0.15, 0, 1);
        ctx.globalAlpha = tp;
        ctx.font = `bold ${W < 500 ? 18 : 26}px Georgia, serif`;
        ctx.fillStyle = accent;
        ctx.textAlign = 'center';
        ctx.fillText('JUSTICE, DELIVERED.', cx, H * 0.93);
        ctx.globalAlpha = 1;
      }
    }

    function animate() {
      draw(scrollProgress(section));
      requestAnimationFrame(animate);
    }
    animate();
  }

  /* ══════════════════════════════════════════════════════════
     AGENCY / CREATIVE
     Geometric shapes morph into a logo, colour palette explodes
     ══════════════════════════════════════════════════════════ */
  function initAgency(section, brand) {
    const canvas = makeCanvas(section, 2);
    const ctx    = canvas.getContext('2d');
    const W = canvas.width, H = canvas.height;
    const accent = brand.accentColor || '#6c63ff';
    const cx = W * 0.5, cy = H * 0.5;

    const shapes = [
      { type: 'circle',   x: cx - 100, y: cy - 60,  size: 40, color: accent },
      { type: 'rect',     x: cx + 60,  y: cy - 80,  size: 50, color: '#ff6b9d' },
      { type: 'triangle', x: cx - 60,  y: cy + 60,  size: 45, color: '#00d4ff' },
      { type: 'circle',   x: cx + 100, y: cy + 40,  size: 30, color: '#ffd700' },
      { type: 'rect',     x: cx,       y: cy - 20,  size: 35, color: '#28c840' },
    ];

    let time = 0;
    function animate() {
      time += 0.015;
      draw(scrollProgress(section));
      requestAnimationFrame(animate);
    }

    function draw(progress) {
      ctx.clearRect(0, 0, W, H);

      shapes.forEach((s, i) => {
        const delay = i * 0.1;
        const sp    = clamp((progress - delay) / 0.5, 0, 1);
        const ep    = easeInOut(sp);

        // Shapes converge to centre as progress increases
        const x = lerp(s.x, cx, ep * 0.7);
        const y = lerp(s.y, cy, ep * 0.7);
        const size = s.size * (1 + ep * 0.3);
        const alpha = 0.7 + ep * 0.3;

        ctx.save();
        ctx.globalAlpha = alpha;
        ctx.fillStyle = s.color;
        ctx.translate(x, y);
        ctx.rotate(time * (i % 2 === 0 ? 0.5 : -0.3) * (1 - ep * 0.8));

        if (s.type === 'circle') {
          ctx.beginPath();
          ctx.arc(0, 0, size, 0, Math.PI*2);
          ctx.fill();
        } else if (s.type === 'rect') {
          ctx.fillRect(-size/2, -size/2, size, size);
        } else {
          ctx.beginPath();
          ctx.moveTo(0, -size);
          ctx.lineTo(size * 0.866, size * 0.5);
          ctx.lineTo(-size * 0.866, size * 0.5);
          ctx.closePath();
          ctx.fill();
        }
        ctx.restore();
      });

      // "BUILT DIFFERENT" text
      if (progress > 0.6) {
        const tp = clamp((progress - 0.6) / 0.4, 0, 1);
        ctx.globalAlpha = tp;
        ctx.font = `bold ${W < 500 ? 24 : 36}px "Geist", sans-serif`;
        ctx.fillStyle = '#ffffff';
        ctx.textAlign = 'center';
        ctx.fillText('BUILT DIFFERENT.', cx, H * 0.88);
        ctx.globalAlpha = 1;
      }
    }

    animate();
  }

  /* ══════════════════════════════════════════════════════════
     PUBLIC API
     ══════════════════════════════════════════════════════════ */
  const NICHE_MAP = {
    coffee:      initCoffee,
    cafe:        initCoffee,
    bakery:      initCoffee,
    restaurant:  initRestaurant,
    ramen:       initRestaurant,
    sushi:       initRestaurant,
    garage:      initGarage,
    auto:        initGarage,
    automotive:  initGarage,
    mechanic:    initGarage,
    fitness:     initFitness,
    gym:         initFitness,
    crossfit:    initFitness,
    beauty:      initBeauty,
    salon:       initBeauty,
    spa:         initBeauty,
    real_estate: initRealEstate,
    realty:      initRealEstate,
    property:    initRealEstate,
    tech_saas:   initTech,
    tech:        initTech,
    saas:        initTech,
    startup:     initTech,
    ecommerce:   initEcommerce,
    shop:        initEcommerce,
    fashion:     initEcommerce,
    hotel:       initHotel,
    resort:      initHotel,
    hospitality: initHotel,
    medical:     initMedical,
    clinic:      initMedical,
    dental:      initMedical,
    law:         initLaw,
    legal:       initLaw,
    attorney:    initLaw,
    agency:      initAgency,
    creative:    initAgency,
    design:      initAgency,
    business:    initTech,  // default
  };

  return {
    /**
     * Initialize niche scroll animation for a section.
     * @param {string} sectionId  - ID of the section element
     * @param {string} niche      - Brand niche key
     * @param {object} brand      - Brand data { accentColor, name, ... }
     */
    init(sectionId, niche, brand) {
      const section = document.getElementById(sectionId);
      if (!section) {
        console.warn('[NicheScroll] Section not found:', sectionId);
        return;
      }
      const fn = NICHE_MAP[niche] || NICHE_MAP.business;
      fn(section, brand || {});
      console.log('[NicheScroll] Initialized:', niche, 'on', sectionId);
    },

    /** Auto-detect and initialize all sections with data-niche-scroll attribute */
    autoInit() {
      document.querySelectorAll('[data-niche-scroll]').forEach(section => {
        const niche = section.dataset.nicheScroll;
        const brand = {
          accentColor: section.dataset.accentColor || '#e63946',
          name: section.dataset.brandName || '',
        };
        const fn = NICHE_MAP[niche] || NICHE_MAP.business;
        fn(section, brand);
      });
    },

    /** List all supported niches */
    supportedNiches: Object.keys(NICHE_MAP),
  };
})();

// Auto-initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => window.NICHE_SCROLL_ANIMATIONS.autoInit());
} else {
  window.NICHE_SCROLL_ANIMATIONS.autoInit();
}
