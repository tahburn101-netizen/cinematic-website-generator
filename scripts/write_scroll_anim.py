"""Write the new scroll-animations.js v2"""
import pathlib

content = r"""/**
 * CINEMATIC SCROLL ANIMATIONS v2 — scroll-animations.js
 * =======================================================
 * Works on mobile AND desktop. No race conditions.
 * Uses IntersectionObserver for reliable reveals.
 * GSAP loaded via <script> tag in <head> — not dynamically.
 */
(function () {
  'use strict';

  /* 1. SCROLL PROGRESS BAR */
  var progressBar = document.getElementById('scroll-progress');
  if (!progressBar) progressBar = document.querySelector('.scroll-progress');
  if (progressBar) {
    progressBar.style.cssText = 'position:fixed;top:0;left:0;height:3px;width:0%;background:var(--accent,#6c63ff);z-index:9999;transition:width 0.1s linear;pointer-events:none;';
    function updateBar() {
      var scrollTop = window.scrollY || document.documentElement.scrollTop;
      var docH = document.documentElement.scrollHeight - window.innerHeight;
      progressBar.style.width = (docH > 0 ? (scrollTop / docH) * 100 : 0) + '%';
    }
    window.addEventListener('scroll', updateBar, { passive: true });
    window.addEventListener('touchmove', updateBar, { passive: true });
  }

  /* 2. INJECT REVEAL CSS */
  if (!document.getElementById('reveal-css')) {
    var s = document.createElement('style');
    s.id = 'reveal-css';
    s.textContent = [
      '.reveal-up{opacity:0;transform:translateY(48px);will-change:opacity,transform;transition:opacity 0.75s cubic-bezier(.22,1,.36,1),transform 0.75s cubic-bezier(.22,1,.36,1);}',
      '.reveal-left{opacity:0;transform:translateX(-48px);will-change:opacity,transform;transition:opacity 0.75s cubic-bezier(.22,1,.36,1),transform 0.75s cubic-bezier(.22,1,.36,1);}',
      '.reveal-right{opacity:0;transform:translateX(48px);will-change:opacity,transform;transition:opacity 0.75s cubic-bezier(.22,1,.36,1),transform 0.75s cubic-bezier(.22,1,.36,1);}',
      '.reveal-scale{opacity:0;transform:scale(0.88);will-change:opacity,transform;transition:opacity 0.75s cubic-bezier(.22,1,.36,1),transform 0.75s cubic-bezier(.22,1,.36,1);}',
      '.is-revealed{opacity:1!important;transform:none!important;}',
    ].join('');
    document.head.appendChild(s);
  }

  /* 3. SECTION REVEALS via IntersectionObserver */
  function initReveals() {
    var els = document.querySelectorAll('.reveal-up,.reveal-left,.reveal-right,.reveal-scale');
    if (!els.length) return;
    if (typeof IntersectionObserver === 'undefined') {
      els.forEach(function(el){ el.classList.add('is-revealed'); });
      return;
    }
    var io = new IntersectionObserver(function(entries) {
      entries.forEach(function(e) {
        if (e.isIntersecting) {
          e.target.classList.add('is-revealed');
          io.unobserve(e.target);
        }
      });
    }, { threshold: 0.08, rootMargin: '0px 0px -32px 0px' });
    els.forEach(function(el){ io.observe(el); });
  }

  /* 4. COUNT-UP STATS */
  function initCountUp() {
    var els = document.querySelectorAll('[data-count-up],.count-up');
    if (!els.length) return;
    var io = new IntersectionObserver(function(entries) {
      entries.forEach(function(e) {
        if (!e.isIntersecting) return;
        io.unobserve(e.target);
        var el = e.target;
        var target = parseFloat(el.getAttribute('data-count-up') || el.getAttribute('data-target') || el.textContent) || 0;
        var suffix = el.getAttribute('data-suffix') || el.getAttribute('data-count-suffix') || '';
        var prefix = el.getAttribute('data-prefix') || el.getAttribute('data-count-prefix') || '';
        var dur = 1800, start = performance.now();
        function step(now) {
          var p = Math.min((now - start) / dur, 1);
          var eased = 1 - Math.pow(1 - p, 3);
          var val = target * eased;
          el.textContent = prefix + (Number.isInteger(target) ? Math.round(val) : val.toFixed(1)) + suffix;
          if (p < 1) requestAnimationFrame(step);
        }
        requestAnimationFrame(step);
      });
    }, { threshold: 0.3 });
    els.forEach(function(el){ io.observe(el); });
  }

  /* 5. MAGNETIC BUTTONS (desktop only) */
  function initMagnetic() {
    if (window.innerWidth < 768) return;
    document.querySelectorAll('.magnetic-btn,[data-magnetic]').forEach(function(btn) {
      btn.addEventListener('mousemove', function(e) {
        var r = btn.getBoundingClientRect();
        var x = (e.clientX - r.left - r.width/2) * 0.28;
        var y = (e.clientY - r.top  - r.height/2) * 0.28;
        btn.style.transform = 'translate('+x+'px,'+y+'px)';
        btn.style.transition = 'transform 0.15s ease';
      });
      btn.addEventListener('mouseleave', function() {
        btn.style.transform = '';
        btn.style.transition = 'transform 0.5s cubic-bezier(.22,1,.36,1)';
      });
    });
  }

  /* 6. TEXT SCRAMBLE — preserves HTML structure */
  function initScramble() {
    var el = document.querySelector('.hero-headline.text-scramble,.text-scramble');
    if (!el) return;
    var originalHTML = el.innerHTML;
    var originalText = el.innerHTML
      .replace(/<br\s*\/?>/gi, ' ')
      .replace(/<[^>]+>/g, '')
      .replace(/\s+/g, ' ')
      .trim();
    var chars = '!<>-_\\/[]{}=+*^?#ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    var queue = [];
    for (var i = 0; i < originalText.length; i++) {
      var st = Math.floor(Math.random() * 18);
      queue.push({ char: originalText[i], start: st, end: st + Math.floor(Math.random() * 12) });
    }
    var frame = 0;
    function update() {
      var out = '', done = 0;
      for (var i = 0; i < queue.length; i++) {
        var q = queue[i];
        if (frame >= q.end) { out += q.char; done++; }
        else { out += q.char === ' ' ? ' ' : chars[Math.floor(Math.random()*chars.length)]; }
      }
      el.textContent = out;
      if (done === queue.length) { el.innerHTML = originalHTML; return; }
      frame++;
      requestAnimationFrame(update);
    }
    setTimeout(function(){ requestAnimationFrame(update); }, 500);
  }

  /* 7. NICHE CANVAS ANIMATION */
  function initNicheCanvas() {
    var section = document.querySelector('[data-niche-scroll]');
    if (!section) return;
    var niche  = section.getAttribute('data-niche-scroll') || 'default';
    var accent = (window.BRAND_DATA && window.BRAND_DATA.accentColor)
                 || getComputedStyle(document.documentElement).getPropertyValue('--accent').trim()
                 || '#6c63ff';

    var hex = accent.replace('#','');
    if (hex.length === 3) hex = hex[0]+hex[0]+hex[1]+hex[1]+hex[2]+hex[2];
    var r = parseInt(hex.slice(0,2),16), g = parseInt(hex.slice(2,4),16), b = parseInt(hex.slice(4,6),16);

    var canvas = document.createElement('canvas');
    canvas.style.cssText = 'position:absolute;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:1;opacity:0.55;';
    section.style.position = 'relative';
    section.style.overflow = 'hidden';
    section.insertBefore(canvas, section.firstChild);

    var ctx = canvas.getContext('2d');
    var W, H, raf = null, progress = 0, tgt = 0;

    function resize() {
      W = canvas.width  = section.offsetWidth  || window.innerWidth;
      H = canvas.height = section.offsetHeight || 500;
    }
    resize();
    window.addEventListener('resize', resize);

    function getP() {
      var rect  = section.getBoundingClientRect();
      var total = section.offsetHeight - window.innerHeight;
      if (total <= 0) return Math.max(0, Math.min(1, 1 - rect.top / window.innerHeight));
      return Math.max(0, Math.min(1, -rect.top / total));
    }
    window.addEventListener('scroll',    function(){ tgt = getP(); }, { passive: true });
    window.addEventListener('touchmove', function(){ tgt = getP(); }, { passive: true });

    function draw() {
      progress += (tgt - progress) * 0.05;
      ctx.clearRect(0,0,W,H);
      var p = progress;
      var t = performance.now() * 0.001;

      if (niche==='restaurant'||niche==='coffee'||niche==='cafe'||niche==='bakery') {
        for (var i=0;i<14;i++) {
          var ph=(i/14)*Math.PI*2;
          var x=W*(0.25+(i/14)*0.5);
          var y=H*0.8-p*H*0.7*((i%3+1)/3);
          var a=p*(1-(y<0?1:y/H))*0.7;
          var sz=3+Math.sin(ph+t*2)*2;
          if(a>0){ctx.beginPath();ctx.arc(x+Math.sin(ph+t*2)*18,y,sz,0,Math.PI*2);ctx.fillStyle='rgba('+r+','+g+','+b+','+a+')';ctx.fill();}
        }
      } else if (niche==='fitness'||niche==='gym') {
        for (var i=0;i<24;i++) {
          var frac=((i/24)+p*0.6)%1;
          var x=W*(0.05+(i/24)*0.9);
          var y=H*(1-frac);
          var a=Math.sin(frac*Math.PI)*p*0.9;
          ctx.beginPath();ctx.arc(x,y,2+frac*5,0,Math.PI*2);ctx.fillStyle='rgba('+r+','+g+','+b+','+a+')';ctx.fill();
        }
      } else if (niche==='beauty'||niche==='skincare') {
        var cx=W*0.5,cy=H*0.5,rad=Math.min(W,H)*0.28*p;
        for (var i=0;i<8;i++) {
          var angle=(i/8)*Math.PI*2+t*0.3;
          var nx=cx+Math.cos(angle)*rad,ny=cy+Math.sin(angle)*rad;
          ctx.beginPath();ctx.arc(nx,ny,7*p,0,Math.PI*2);ctx.fillStyle='rgba('+r+','+g+','+b+','+(p*0.8)+')';ctx.fill();
          if(i>0){var pa=((i-1)/8)*Math.PI*2+t*0.3;ctx.beginPath();ctx.moveTo(cx+Math.cos(pa)*rad,cy+Math.sin(pa)*rad);ctx.lineTo(nx,ny);ctx.strokeStyle='rgba('+r+','+g+','+b+','+(p*0.3)+')';ctx.lineWidth=1;ctx.stroke();}
        }
      } else if (niche==='tech'||niche==='saas'||niche==='tech_saas') {
        for (var i=0;i<8;i++) {
          var sy=H*(0.15+(i/8)*0.7);
          var ex=W*p;
          ctx.beginPath();ctx.moveTo(0,sy);ctx.lineTo(ex,sy);ctx.strokeStyle='rgba('+r+','+g+','+b+','+(0.3+i*0.04)+')';ctx.lineWidth=1.5;ctx.stroke();
          if(p>0.05){ctx.beginPath();ctx.arc(ex,sy,3,0,Math.PI*2);ctx.fillStyle='rgba('+r+','+g+','+b+',0.9)';ctx.fill();}
        }
      } else if (niche==='automotive'||niche==='garage') {
        var cx=W*0.5,cy=H*0.5,rad=Math.min(W,H)*0.3*p;
        for (var i=0;i<6;i++) {
          var angle=(i/6)*Math.PI*2+t*0.5;
          var nx=cx+Math.cos(angle)*rad,ny=cy+Math.sin(angle)*rad;
          ctx.save();ctx.translate(nx,ny);ctx.rotate(angle);ctx.fillStyle='rgba('+r+','+g+','+b+','+(p*0.65)+')';ctx.fillRect(-9,-5,18,10);ctx.restore();
        }
      } else {
        var pts=[];
        for(var i=0;i<10;i++) pts.push({x:W*(0.08+(i/10)*0.84),y:H*(0.3+Math.sin(i*1.2)*0.3)});
        var to=Math.floor(p*(pts.length-1));
        for(var i=0;i<=to;i++){
          ctx.beginPath();ctx.arc(pts[i].x,pts[i].y,4,0,Math.PI*2);ctx.fillStyle='rgba('+r+','+g+','+b+',0.8)';ctx.fill();
          if(i>0){ctx.beginPath();ctx.moveTo(pts[i-1].x,pts[i-1].y);ctx.lineTo(pts[i].x,pts[i].y);ctx.strokeStyle='rgba('+r+','+g+','+b+',0.3)';ctx.lineWidth=1;ctx.stroke();}
        }
      }
    }

    function loop() { raf=requestAnimationFrame(loop); draw(); }

    if (typeof IntersectionObserver !== 'undefined') {
      new IntersectionObserver(function(entries){
        if(entries[0].isIntersecting){if(!raf)loop();}
        else{cancelAnimationFrame(raf);raf=null;}
      },{threshold:0}).observe(section);
    } else { loop(); }
  }

  /* 8. GSAP ENHANCEMENTS (only if already loaded) */
  function initGSAP() {
    if (!window.gsap || !window.ScrollTrigger) return;
    gsap.registerPlugin(ScrollTrigger);
    gsap.utils.toArray('.parallax-img').forEach(function(img){
      gsap.to(img,{yPercent:-20,ease:'none',scrollTrigger:{trigger:img,start:'top bottom',end:'bottom top',scrub:true}});
    });
  }

  /* BOOT */
  function boot() {
    initReveals();
    initCountUp();
    initMagnetic();
    initScramble();
    initNicheCanvas();
    if (window.gsap) initGSAP();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
"""

out = pathlib.Path('/home/ubuntu/cinematic-pipeline/cinematic-modules/scroll-animations.js')
out.write_text(content)
print(f'Written {len(content.splitlines())} lines to {out}')
