import{D as h,E as qe,I as le,J as Vt,Q as Ot,V as $t,Vt as Mt,W as Me,X as Ge,bt as N,ct as Lt,et as jt,q as Qe,st as ae,ut as Ut,wt as Bt,z as w}from"./editor-BzczECHk.js";import{A as ze,E as Wt,Kt as Zt,Ut as Xt,dt as Le,h as et,ht as Yt,i as Kt,st as Ft}from"./naive-ui-alert-47JY8xkM.js";import{_ as A,b as c,c as ue,p as Ht,v as Jt,x as d}from"./naive-ui-affix-DrKOrtjc.js";import{R as qt,at as Gt}from"./naive-ui-auto-complete-CCvmg59k.js";import{S as Qt,b as q,f as je,u as Ue,x as G}from"./naive-ui-anchor-CMhXUotn.js";function ao(e=8){return Math.random().toString(16).slice(2,2+e)}function io(e,n){const o=[];for(let i=0;i<e;++i)o.push(n);return o}function en(e,n){const o=[];if(!n){for(let i=0;i<e;++i)o.push(i);return o}for(let i=0;i<e;++i)o.push(n(i));return o}function tn(e){return Wt(ze(e).toLowerCase())}function nn(e,n,o,i){var f=-1,g=e==null?0:e.length;for(i&&g&&(o=e[++f]);++f<g;)o=n(o,e[f],f,e);return o}function on(e){return function(n){return e?.[n]}}var rn=on({À:"A",Á:"A",Â:"A",Ã:"A",Ä:"A",Å:"A",à:"a",á:"a",â:"a",ã:"a",ä:"a",å:"a",Ç:"C",ç:"c",Ð:"D",ð:"d",È:"E",É:"E",Ê:"E",Ë:"E",è:"e",é:"e",ê:"e",ë:"e",Ì:"I",Í:"I",Î:"I",Ï:"I",ì:"i",í:"i",î:"i",ï:"i",Ñ:"N",ñ:"n",Ò:"O",Ó:"O",Ô:"O",Õ:"O",Ö:"O",Ø:"O",ò:"o",ó:"o",ô:"o",õ:"o",ö:"o",ø:"o",Ù:"U",Ú:"U",Û:"U",Ü:"U",ù:"u",ú:"u",û:"u",ü:"u",Ý:"Y",ý:"y",ÿ:"y",Æ:"Ae",æ:"ae",Þ:"Th",þ:"th",ß:"ss",Ā:"A",Ă:"A",Ą:"A",ā:"a",ă:"a",ą:"a",Ć:"C",Ĉ:"C",Ċ:"C",Č:"C",ć:"c",ĉ:"c",ċ:"c",č:"c",Ď:"D",Đ:"D",ď:"d",đ:"d",Ē:"E",Ĕ:"E",Ė:"E",Ę:"E",Ě:"E",ē:"e",ĕ:"e",ė:"e",ę:"e",ě:"e",Ĝ:"G",Ğ:"G",Ġ:"G",Ģ:"G",ĝ:"g",ğ:"g",ġ:"g",ģ:"g",Ĥ:"H",Ħ:"H",ĥ:"h",ħ:"h",Ĩ:"I",Ī:"I",Ĭ:"I",Į:"I",İ:"I",ĩ:"i",ī:"i",ĭ:"i",į:"i",ı:"i",Ĵ:"J",ĵ:"j",Ķ:"K",ķ:"k",ĸ:"k",Ĺ:"L",Ļ:"L",Ľ:"L",Ŀ:"L",Ł:"L",ĺ:"l",ļ:"l",ľ:"l",ŀ:"l",ł:"l",Ń:"N",Ņ:"N",Ň:"N",Ŋ:"N",ń:"n",ņ:"n",ň:"n",ŋ:"n",Ō:"O",Ŏ:"O",Ő:"O",ō:"o",ŏ:"o",ő:"o",Ŕ:"R",Ŗ:"R",Ř:"R",ŕ:"r",ŗ:"r",ř:"r",Ś:"S",Ŝ:"S",Ş:"S",Š:"S",ś:"s",ŝ:"s",ş:"s",š:"s",Ţ:"T",Ť:"T",Ŧ:"T",ţ:"t",ť:"t",ŧ:"t",Ũ:"U",Ū:"U",Ŭ:"U",Ů:"U",Ű:"U",Ų:"U",ũ:"u",ū:"u",ŭ:"u",ů:"u",ű:"u",ų:"u",Ŵ:"W",ŵ:"w",Ŷ:"Y",ŷ:"y",Ÿ:"Y",Ź:"Z",Ż:"Z",Ž:"Z",ź:"z",ż:"z",ž:"z",Ĳ:"IJ",ĳ:"ij",Œ:"Oe",œ:"oe",ŉ:"'n",ſ:"s"}),an=/[\xc0-\xd6\xd8-\xf6\xf8-\xff\u0100-\u017f]/g,sn=RegExp("[\\u0300-\\u036f\\ufe20-\\ufe2f\\u20d0-\\u20ff]","g");function ln(e){return e=ze(e),e&&e.replace(an,rn).replace(sn,"")}var un=/[^\x00-\x2f\x3a-\x40\x5b-\x60\x7b-\x7f]+/g;function cn(e){return e.match(un)||[]}var dn=/[a-z][A-Z]|[A-Z]{2}[a-z]|[0-9][a-zA-Z]|[a-zA-Z][0-9]|[^a-zA-Z0-9 ]/;function fn(e){return dn.test(e)}var tt="\\ud800-\\udfff",vn="\\u0300-\\u036f\\ufe20-\\ufe2f\\u20d0-\\u20ff",nt="\\u2700-\\u27bf",ot="a-z\\xdf-\\xf6\\xf8-\\xff",hn="\\xac\\xb1\\xd7\\xf7",pn="\\x00-\\x2f\\x3a-\\x40\\x5b-\\x60\\x7b-\\xbf",gn="\\u2000-\\u206f",xn=" \\t\\x0b\\f\\xa0\\ufeff\\n\\r\\u2028\\u2029\\u1680\\u180e\\u2000\\u2001\\u2002\\u2003\\u2004\\u2005\\u2006\\u2007\\u2008\\u2009\\u200a\\u202f\\u205f\\u3000",rt="A-Z\\xc0-\\xd6\\xd8-\\xde",mn="\\ufe0e\\ufe0f",at=hn+pn+gn+xn,it="['’]",Be="["+at+"]",bn="["+vn+"]",st="\\d+",wn="["+nt+"]",lt="["+ot+"]",ut="[^"+tt+at+st+nt+ot+rt+"]",yn="(?:"+bn+"|\\ud83c[\\udffb-\\udfff])",Sn="[^"+tt+"]",ct="(?:\\ud83c[\\udde6-\\uddff]){2}",dt="[\\ud800-\\udbff][\\udc00-\\udfff]",Y="["+rt+"]",Cn="\\u200d",We="(?:"+lt+"|"+ut+")",Rn="(?:"+Y+"|"+ut+")",Ze="(?:"+it+"(?:d|ll|m|re|s|t|ve))?",Xe="(?:"+it+"(?:D|LL|M|RE|S|T|VE))?",ft=yn+"?",vt="["+mn+"]?",zn="(?:"+Cn+"(?:"+[Sn,ct,dt].join("|")+")"+vt+ft+")*",Pn="\\d*(?:1st|2nd|3rd|(?![123])\\dth)(?=\\b|[A-Z_])",In="\\d*(?:1ST|2ND|3RD|(?![123])\\dTH)(?=\\b|[a-z_])",Dn=vt+ft+zn,kn="(?:"+[wn,ct,dt].join("|")+")"+Dn,An=RegExp([Y+"?"+lt+"+"+Ze+"(?="+[Be,Y,"$"].join("|")+")",Rn+"+"+Xe+"(?="+[Be,Y+We,"$"].join("|")+")",Y+"?"+We+"+"+Ze,Y+"+"+Xe,In,Pn,st,kn].join("|"),"g");function En(e){return e.match(An)||[]}function Tn(e,n,o){return e=ze(e),n=o?void 0:n,n===void 0?fn(e)?En(e):cn(e):e.match(n)||[]}var Nn=RegExp("['’]","g");function _n(e){return function(n){return nn(Tn(ln(n).replace(Nn,"")),e,"")}}var Ye=_n(function(e,n,o){return n=n.toLowerCase(),e+(o?tn(n):n)});function Vn(){return{dotSize:"8px",dotColor:"rgba(255, 255, 255, .3)",dotColorActive:"rgba(255, 255, 255, 1)",dotColorFocus:"rgba(255, 255, 255, .5)",dotLineWidth:"16px",dotLineWidthActive:"24px",arrowColor:"#eee"}}var On={name:"Carousel",common:Kt,self:Vn},ht=Ht("n-carousel-methods");function $n(e){jt(ht,e)}function Pe(e="unknown",n="component"){const o=$t(ht);return o||Yt(e,`\`${n}\` must be placed inside \`n-carousel\`.`),o}function Mn(){return w("svg",{xmlns:"http://www.w3.org/2000/svg",viewBox:"0 0 16 16"},w("g",{fill:"none"},w("path",{d:"M10.26 3.2a.75.75 0 0 1 .04 1.06L6.773 8l3.527 3.74a.75.75 0 1 1-1.1 1.02l-4-4.25a.75.75 0 0 1 0-1.02l4-4.25a.75.75 0 0 1 1.06-.04z",fill:"currentColor"})))}function Ln(){return w("svg",{xmlns:"http://www.w3.org/2000/svg",viewBox:"0 0 16 16"},w("g",{fill:"none"},w("path",{d:"M5.74 3.2a.75.75 0 0 0-.04 1.06L9.227 8L5.7 11.74a.75.75 0 1 0 1.1 1.02l4-4.25a.75.75 0 0 0 0-1.02l-4-4.25a.75.75 0 0 0-1.06-.04z",fill:"currentColor"})))}var jn=le({name:"CarouselArrow",setup(e){const{mergedClsPrefixRef:n}=ue(e),{isVertical:o,isPrevDisabled:i,isNextDisabled:f,prev:g,next:z}=Pe();return{mergedClsPrefix:n,isVertical:o,isPrevDisabled:i,isNextDisabled:f,prev:g,next:z}},render(){const{mergedClsPrefix:e}=this;return w("div",{class:`${e}-carousel__arrow-group`},w("div",{class:[`${e}-carousel__arrow`,this.isPrevDisabled()&&`${e}-carousel__arrow--disabled`],role:"button",onClick:this.prev},Mn()),w("div",{class:[`${e}-carousel__arrow`,this.isNextDisabled()&&`${e}-carousel__arrow--disabled`],role:"button",onClick:this.next},Ln()))}}),Un={total:{type:Number,default:0},currentIndex:{type:Number,default:0},dotType:{type:String,default:"dot"},trigger:{type:String,default:"click"},keyboard:Boolean},Bn=le({name:"CarouselDots",props:Un,setup(e){const{mergedClsPrefixRef:n}=ue(e),o=N([]),i=Pe();function f(x,v){switch(x.key){case"Enter":case" ":x.preventDefault(),i.to(v);return}e.keyboard&&y(x)}function g(x){e.trigger==="hover"&&i.to(x)}function z(x){e.trigger==="click"&&i.to(x)}function y(x){var v;if(x.shiftKey||x.altKey||x.ctrlKey||x.metaKey)return;const b=(v=document.activeElement)===null||v===void 0?void 0:v.nodeName.toLowerCase();if(b==="input"||b==="textarea")return;const{code:C}=x,$=C==="PageUp"||C==="ArrowUp",M=C==="PageDown"||C==="ArrowDown",S=C==="PageUp"||C==="ArrowRight",R=C==="PageDown"||C==="ArrowLeft",_=i.isVertical(),L=_?$:S,V=_?M:R;!L&&!V||(x.preventDefault(),L&&!i.isNextDisabled()?(i.next(),P(i.currentIndexRef.value)):V&&!i.isPrevDisabled()&&(i.prev(),P(i.currentIndexRef.value)))}function P(x){var v;(v=o.value[x])===null||v===void 0||v.focus()}return Vt(()=>o.value.length=0),{mergedClsPrefix:n,dotEls:o,handleKeydown:f,handleMouseenter:g,handleClick:z}},render(){const{mergedClsPrefix:e,dotEls:n}=this;return w("div",{class:[`${e}-carousel__dots`,`${e}-carousel__dots--${this.dotType}`],role:"tablist"},en(this.total,o=>{const i=o===this.currentIndex;return w("div",{"aria-selected":i,ref:f=>n.push(f),role:"button",tabindex:"0",class:[`${e}-carousel__dot`,i&&`${e}-carousel__dot--active`],key:o,onClick:()=>{this.handleClick(o)},onMouseenter:()=>{this.handleMouseenter(o)},onKeydown:f=>{this.handleKeydown(f,o)}})}))}}),se="CarouselItem";function Wn(e){var n;return((n=e.type)===null||n===void 0?void 0:n.name)===se}var Zn=le({name:se,setup(e){const{mergedClsPrefixRef:n}=ue(e),o=Pe(Ye(se),`n-${Ye(se)}`),i=N(),f=h(()=>{const{value:v}=i;return v?o.getSlideIndex(v):-1}),g=h(()=>o.isPrev(f.value)),z=h(()=>o.isNext(f.value)),y=h(()=>o.isActive(f.value)),P=h(()=>o.getSlideStyle(f.value));Ge(()=>{o.addSlide(i.value)}),Qe(()=>{o.removeSlide(i.value)});function x(v){const{value:b}=f;b!==void 0&&o?.onCarouselItemClick(b,v)}return{mergedClsPrefix:n,selfElRef:i,isPrev:g,isNext:z,isActive:y,index:f,style:P,handleClick:x}},render(){var e;const{$slots:n,mergedClsPrefix:o,isPrev:i,isNext:f,isActive:g,index:z,style:y}=this;return w("div",{ref:"selfElRef",class:[`${o}-carousel__slide`,{[`${o}-carousel__slide--current`]:g,[`${o}-carousel__slide--prev`]:i,[`${o}-carousel__slide--next`]:f}],role:"option",tabindex:"-1","data-index":z,"aria-hidden":!g,style:y,onClickCapture:this.handleClick},(e=n.default)===null||e===void 0?void 0:e.call(n,{isPrev:i,isNext:f,isActive:g,index:z}))}}),Xn=Jt("carousel",`
 position: relative;
 width: 100%;
 height: 100%;
 touch-action: pan-y;
 overflow: hidden;
`,[c("slides",`
 display: flex;
 width: 100%;
 height: 100%;
 transition-timing-function: var(--n-bezier);
 transition-property: transform;
 `,[c("slide",`
 flex-shrink: 0;
 position: relative;
 width: 100%;
 height: 100%;
 outline: none;
 overflow: hidden;
 `,[A("> img",`
 display: block;
 `)])]),c("dots",`
 position: absolute;
 display: flex;
 flex-wrap: nowrap;
 `,[d("dot",[c("dot",`
 height: var(--n-dot-size);
 width: var(--n-dot-size);
 background-color: var(--n-dot-color);
 border-radius: 50%;
 cursor: pointer;
 transition:
 box-shadow .3s var(--n-bezier),
 background-color .3s var(--n-bezier);
 outline: none;
 `,[A("&:focus",`
 background-color: var(--n-dot-color-focus);
 `),d("active",`
 background-color: var(--n-dot-color-active);
 `)])]),d("line",[c("dot",`
 border-radius: 9999px;
 width: var(--n-dot-line-width);
 height: 4px;
 background-color: var(--n-dot-color);
 cursor: pointer;
 transition:
 width .3s var(--n-bezier),
 box-shadow .3s var(--n-bezier),
 background-color .3s var(--n-bezier);
 outline: none;
 `,[A("&:focus",`
 background-color: var(--n-dot-color-focus);
 `),d("active",`
 width: var(--n-dot-line-width-active);
 background-color: var(--n-dot-color-active);
 `)])])]),c("arrow",`
 transition: background-color .3s var(--n-bezier);
 cursor: pointer;
 height: 28px;
 width: 28px;
 display: flex;
 align-items: center;
 justify-content: center;
 background-color: rgba(255, 255, 255, .2);
 color: var(--n-arrow-color);
 border-radius: 8px;
 user-select: none;
 -webkit-user-select: none;
 font-size: 18px;
 `,[A("svg",`
 height: 1em;
 width: 1em;
 `),A("&:hover",`
 background-color: rgba(255, 255, 255, .3);
 `)]),d("vertical",`
 touch-action: pan-x;
 `,[c("slides",`
 flex-direction: column;
 `),d("fade",[c("slide",`
 top: 50%;
 left: unset;
 transform: translateY(-50%);
 `)]),d("card",[c("slide",`
 top: 50%;
 left: unset;
 transform: translateY(-50%) translateZ(-400px);
 `,[d("current",`
 transform: translateY(-50%) translateZ(0);
 `),d("prev",`
 transform: translateY(-100%) translateZ(-200px);
 `),d("next",`
 transform: translateY(0%) translateZ(-200px);
 `)])])]),d("usercontrol",[c("slides",[A(">",[A("div",`
 position: absolute;
 top: 50%;
 left: 50%;
 width: 100%;
 height: 100%;
 transform: translate(-50%, -50%);
 `)])])]),d("left",[c("dots",`
 transform: translateY(-50%);
 top: 50%;
 left: 12px;
 flex-direction: column;
 `,[d("line",[c("dot",`
 width: 4px;
 height: var(--n-dot-line-width);
 margin: 4px 0;
 transition:
 height .3s var(--n-bezier),
 box-shadow .3s var(--n-bezier),
 background-color .3s var(--n-bezier);
 outline: none;
 `,[d("active",`
 height: var(--n-dot-line-width-active);
 `)])])]),c("dot",`
 margin: 4px 0;
 `)]),c("arrow-group",`
 position: absolute;
 display: flex;
 flex-wrap: nowrap;
 `),d("vertical",[c("arrow",`
 transform: rotate(90deg);
 `)]),d("show-arrow",[d("bottom",[c("dots",`
 transform: translateX(0);
 bottom: 18px;
 left: 18px;
 `)]),d("top",[c("dots",`
 transform: translateX(0);
 top: 18px;
 left: 18px;
 `)]),d("left",[c("dots",`
 transform: translateX(0);
 top: 18px;
 left: 18px;
 `)]),d("right",[c("dots",`
 transform: translateX(0);
 top: 18px;
 right: 18px;
 `)])]),d("left",[c("arrow-group",`
 bottom: 12px;
 left: 12px;
 flex-direction: column;
 `,[A("> *:first-child",`
 margin-bottom: 12px;
 `)])]),d("right",[c("dots",`
 transform: translateY(-50%);
 top: 50%;
 right: 12px;
 flex-direction: column;
 `,[d("line",[c("dot",`
 width: 4px;
 height: var(--n-dot-line-width);
 margin: 4px 0;
 transition:
 height .3s var(--n-bezier),
 box-shadow .3s var(--n-bezier),
 background-color .3s var(--n-bezier);
 outline: none;
 `,[d("active",`
 height: var(--n-dot-line-width-active);
 `)])])]),c("dot",`
 margin: 4px 0;
 `),c("arrow-group",`
 bottom: 12px;
 right: 12px;
 flex-direction: column;
 `,[A("> *:first-child",`
 margin-bottom: 12px;
 `)])]),d("top",[c("dots",`
 transform: translateX(-50%);
 top: 12px;
 left: 50%;
 `,[d("line",[c("dot",`
 margin: 0 4px;
 `)])]),c("dot",`
 margin: 0 4px;
 `),c("arrow-group",`
 top: 12px;
 right: 12px;
 `,[A("> *:first-child",`
 margin-right: 12px;
 `)])]),d("bottom",[c("dots",`
 transform: translateX(-50%);
 bottom: 12px;
 left: 50%;
 `,[d("line",[c("dot",`
 margin: 0 4px;
 `)])]),c("dot",`
 margin: 0 4px;
 `),c("arrow-group",`
 bottom: 12px;
 right: 12px;
 `,[A("> *:first-child",`
 margin-right: 12px;
 `)])]),d("fade",[c("slide",`
 position: absolute;
 opacity: 0;
 transition-property: opacity;
 pointer-events: none;
 `,[d("current",`
 opacity: 1;
 pointer-events: auto;
 `)])]),d("card",[c("slides",`
 perspective: 1000px;
 `),c("slide",`
 position: absolute;
 left: 50%;
 opacity: 0;
 transform: translateX(-50%) translateZ(-400px);
 transition-property: opacity, transform;
 `,[d("current",`
 opacity: 1;
 transform: translateX(-50%) translateZ(0);
 z-index: 1;
 `),d("prev",`
 opacity: 0.4;
 transform: translateX(-100%) translateZ(-200px);
 `),d("next",`
 opacity: 0.4;
 transform: translateX(0%) translateZ(-200px);
 `)])])]);function Yn(e){const{length:n}=e;return n>1&&(e.push(Ke(e[0],0,"append")),e.unshift(Ke(e[n-1],n-1,"prepend"))),e}function Ke(e,n,o){return qe(e,{key:`carousel-item-duplicate-${n}-${o}`})}function Fe(e,n,o){return n===1?0:o?e===0?n-3:e===n-1?0:e-1:e}function Ce(e,n){return n?e+1:e}function Kn(e,n,o){return e<0?null:e===0?o?n-1:null:e-1}function Fn(e,n,o){return e>n-1?null:e===n-1?o?0:null:e+1}function Hn(e,n){return n&&e>3?e-2:e}function He(e){return window.TouchEvent&&e instanceof window.TouchEvent}function Je(e,n){let{offsetWidth:o,offsetHeight:i}=e;if(n){const f=getComputedStyle(e);o=o-Number.parseFloat(f.getPropertyValue("padding-left"))-Number.parseFloat(f.getPropertyValue("padding-right")),i=i-Number.parseFloat(f.getPropertyValue("padding-top"))-Number.parseFloat(f.getPropertyValue("padding-bottom"))}return{width:o,height:i}}function ie(e,n,o){return e<n?n:e>o?o:e}function Jn(e){if(e===void 0)return 0;if(typeof e=="number")return e;const n=e.match(/^((\d+)?\.?\d+?)(ms|s)?$/);if(n){const[,o,,i="ms"]=n;return Number(o)*(i==="ms"?1:1e3)}return 0}var qn=["transitionDuration","transitionTimingFunction"],Gn=Object.assign(Object.assign({},et.props),{defaultIndex:{type:Number,default:0},currentIndex:Number,showArrow:Boolean,dotType:{type:String,default:"dot"},dotPlacement:{type:String,default:"bottom"},slidesPerView:{type:[Number,String],default:1},spaceBetween:{type:Number,default:0},centeredSlides:Boolean,direction:{type:String,default:"horizontal"},autoplay:Boolean,interval:{type:Number,default:5e3},loop:{type:Boolean,default:!0},effect:{type:String,default:"slide"},showDots:{type:Boolean,default:!0},trigger:{type:String,default:"click"},transitionStyle:{type:Object,default:()=>({transitionDuration:"300ms"})},transitionProps:Object,draggable:Boolean,prevSlideStyle:[Object,String],nextSlideStyle:[Object,String],touchable:{type:Boolean,default:!0},mousewheel:Boolean,keyboard:Boolean,"onUpdate:currentIndex":Function,onUpdateCurrentIndex:Function}),Re=!1,so=le({name:"Carousel",props:Gn,slots:Object,setup(e){const{mergedClsPrefixRef:n,inlineThemeDisabled:o}=ue(e),i=N(null),f=N(null),g=N([]),z={value:[]},y=h(()=>e.direction==="vertical"),P=h(()=>y.value?"height":"width"),x=h(()=>y.value?"bottom":"right"),v=h(()=>e.effect==="slide"),b=h(()=>e.loop&&e.slidesPerView===1&&v.value),C=h(()=>e.effect==="custom"),$=h(()=>!v.value||e.centeredSlides?1:e.slidesPerView),M=h(()=>C.value?1:e.slidesPerView),S=h(()=>$.value==="auto"||e.slidesPerView==="auto"&&e.centeredSlides),R=N({width:0,height:0}),_=N(0),L=h(()=>{const{value:t}=g;if(!t.length)return[];_.value;const{value:r}=S;if(r)return t.map(m=>Je(m));const{value:a}=M,{value:l}=R,{value:u}=P;let s=l[u];if(a!=="auto"){const{spaceBetween:m}=e;s=(s-(a-1)*m)*(1/Math.max(1,a))}const p=Object.assign(Object.assign({},l),{[u]:s});return t.map(()=>p)}),V=h(()=>{const{value:t}=L;if(!t.length)return[];const{centeredSlides:r,spaceBetween:a}=e,{value:l}=P,{[l]:u}=R.value;let s=0;return t.map(({[l]:p})=>{let m=s;return r&&(m+=(p-u)/2),s+=p+a,m})}),Ie=N(!1),ce=h(()=>{const{transitionStyle:t}=e;return t?Ue(t,qn):{}}),de=h(()=>C.value?0:Jn(ce.value.transitionDuration)),De=h(()=>{const{value:t}=g;if(!t.length)return[];const r=!(S.value||M.value===1),a=p=>{if(r){const{value:m}=P;return{[m]:`${L.value[p][m]}px`}}};if(C.value)return t.map((p,m)=>a(m));const{effect:l,spaceBetween:u}=e,{value:s}=x;return t.reduce((p,m,T)=>{const $e=Object.assign(Object.assign({},a(T)),{[`margin-${s}`]:`${u}px`});return p.push($e),Ie.value&&(l==="fade"||l==="card")&&Object.assign($e,ce.value),p},[])}),I=h(()=>{const{value:t}=$,{length:r}=g.value;if(t!=="auto")return Math.max(r-t,0)+1;{const{value:a}=L,{length:l}=a;if(!l)return r;const{value:u}=V,{value:s}=P,p=R.value[s];let m=a[a.length-1][s],T=l;for(;T>1&&m<p;)T--,m+=u[T]-u[T-1];return ie(T+1,1,l)}}),fe=h(()=>Hn(I.value,b.value)),ve=N(Fe(Ce(e.defaultIndex,b.value),I.value,b.value)),E=Gt(Bt(e,"currentIndex"),ve),D=h(()=>Ce(E.value,b.value));function K(t){var r,a;t=ie(t,0,I.value-1);const l=Fe(t,I.value,b.value),{value:u}=E;l!==E.value&&(ve.value=l,(r=e["onUpdate:currentIndex"])===null||r===void 0||r.call(e,l,u),(a=e.onUpdateCurrentIndex)===null||a===void 0||a.call(e,l,u))}function he(t=D.value){return Kn(t,I.value,e.loop)}function pe(t=D.value){return Fn(t,I.value,e.loop)}function pt(t){const r=B(t);return r!==null&&he()===r&&I.value>1}function gt(t){const r=B(t);return r!==null&&pe()===r&&I.value>1}function ke(t){return D.value===B(t)}function xt(t){return E.value===t}function Ae(){return he()===null}function Ee(){return pe()===null}let U=0;function ge(t){const r=ie(Ce(t,b.value),0,I.value);(t!==E.value||r!==D.value)&&K(r)}function Q(){const t=he();t!==null&&(U=-1,K(t))}function F(){const t=pe();t!==null&&(U=1,K(t))}let k=!1;function mt(){(!k||!b.value)&&Q()}function bt(){(!k||!b.value)&&F()}let j=0;const xe=N({});function ee(t,r=0){xe.value=Object.assign({},ce.value,{transform:y.value?`translateY(${-t}px)`:`translateX(${-t}px)`,transitionDuration:`${r}ms`})}function H(t=0){v.value?me(D.value,t):j!==0&&(!k&&t>0&&(k=!0),ee(j=0,t))}function me(t,r){const a=Te(t);a!==j&&r>0&&(k=!0),j=Te(D.value),ee(a,r)}function Te(t){let r;return t>=I.value-1?r=Ne():r=V.value[t]||0,r}function Ne(){if($.value==="auto"){const{value:t}=P,{[t]:r}=R.value,{value:a}=V,l=a[a.length-1];let u;if(l===void 0)u=r;else{const{value:s}=L;u=l+s[s.length-1][t]}return u-r}else{const{value:t}=V;return t[I.value-1]||0}}const J={currentIndexRef:E,to:ge,prev:mt,next:bt,isVertical:()=>y.value,isHorizontal:()=>!y.value,isPrev:pt,isNext:gt,isActive:ke,isPrevDisabled:Ae,isNextDisabled:Ee,getSlideIndex:B,getSlideStyle:St,addSlide:wt,removeSlide:yt,onCarouselItemClick:Ct};$n(J);function wt(t){t&&g.value.push(t)}function yt(t){if(!t)return;const r=B(t);r!==-1&&g.value.splice(r,1)}function B(t){return typeof t=="number"?t:t?g.value.indexOf(t):-1}function St(t){const r=B(t);if(r!==-1){const a=[De.value[r]],l=J.isPrev(r),u=J.isNext(r);return l&&a.push(e.prevSlideStyle||""),u&&a.push(e.nextSlideStyle||""),Mt(a)}}let be=0,we=0,O=0,ye=0,te=!1,Se=!1;function Ct(t,r){let a=!k&&!te&&!Se;e.effect==="card"&&a&&!ke(t)&&(ge(t),a=!1),a||(r.preventDefault(),r.stopPropagation())}let ne=null;function oe(){ne&&(clearInterval(ne),ne=null)}function W(){oe(),!e.autoplay||fe.value<2||(ne=window.setInterval(F,e.interval))}function _e(t){var r;if(Re||!(!((r=f.value)===null||r===void 0)&&r.contains(Qt(t))))return;Re=!0,te=!0,Se=!1,ye=Date.now(),oe(),t.type!=="touchstart"&&!t.target.isContentEditable&&t.preventDefault();const a=He(t)?t.touches[0]:t;y.value?we=a.clientY:be=a.clientX,e.touchable&&(G("touchmove",document,re),G("touchend",document,Z),G("touchcancel",document,Z)),e.draggable&&(G("mousemove",document,re),G("mouseup",document,Z))}function re(t){const{value:r}=y,{value:a}=P,l=He(t)?t.touches[0]:t,u=r?l.clientY-we:l.clientX-be,s=R.value[a];O=ie(u,-s,s),t.cancelable&&t.preventDefault(),v.value&&ee(j-O,0)}function Z(){const{value:t}=D;let r=t;if(!k&&O!==0&&v.value){const a=j-O,l=[...V.value.slice(0,I.value-1),Ne()];let u=null;for(let s=0;s<l.length;s++){const p=Math.abs(l[s]-a);if(u!==null&&u<p)break;u=p,r=s}}if(r===t){const a=Date.now()-ye,{value:l}=P,u=R.value[l];O>u/2||O/a>.4?Q():(O<-u/2||O/a<-.4)&&F()}r!==null&&r!==t?(Se=!0,K(r),Me(()=>{(!b.value||ve.value!==E.value)&&H(de.value)})):H(de.value),Ve(),W()}function Ve(){te&&(Re=!1),te=!1,be=0,we=0,O=0,ye=0,q("touchmove",document,re),q("touchend",document,Z),q("touchcancel",document,Z),q("mousemove",document,re),q("mouseup",document,Z)}function Rt(){if(v.value&&k){const{value:t}=D;me(t,0)}else W();v.value&&(xe.value.transitionDuration="0ms"),k=!1}function zt(t){if(t.preventDefault(),k)return;let{deltaX:r,deltaY:a}=t;t.shiftKey&&!r&&(r=a);const l=-1,u=1,s=(r||a)>0?u:l;let p=0,m=0;y.value?m=s:p=s;const T=10;(m*a>=T||p*r>=T)&&(s===u&&!Ee()?F():s===l&&!Ae()&&Q())}function Pt(){R.value=Je(i.value,!0),W()}function It(){S.value&&_.value++}function Dt(){e.autoplay&&oe()}function kt(){e.autoplay&&W()}Ge(()=>{Lt(W),requestAnimationFrame(()=>Ie.value=!0)}),Qe(()=>{Ve(),oe()}),Ot(()=>{const{value:t}=g,{value:r}=z,a=new Map,l=s=>a.has(s)?a.get(s):-1;let u=!1;for(let s=0;s<t.length;s++){const p=r.findIndex(m=>m.el===t[s]);p!==s&&(u=!0),a.set(t[s],p)}u&&t.sort((s,p)=>l(s)-l(p))}),ae(D,(t,r)=>{if(t===r){U=0;return}if(W(),v.value){if(b.value){const{value:a}=I;U===-1&&r===1&&t===a-2?t=0:U===1&&r===a-2&&t===1&&(t=a-1)}me(t,de.value)}else H();U=0},{immediate:!0}),ae([b,$],()=>{Me(()=>{K(D.value)})}),ae(V,()=>{v.value&&H()},{deep:!0}),ae(v,t=>{t?H():(k=!1,ee(j=0))});const At=h(()=>({onTouchstartPassive:e.touchable?_e:void 0,onMousedown:e.draggable?_e:void 0,onWheel:e.mousewheel?zt:void 0})),Et=h(()=>Object.assign(Object.assign({},Ue(J,["to","prev","next","isPrevDisabled","isNextDisabled"])),{total:fe.value,currentIndex:E.value})),Tt=h(()=>({total:fe.value,currentIndex:E.value,to:J.to})),Nt={getCurrentIndex:()=>E.value,to:ge,prev:Q,next:F},_t=et("Carousel","-carousel",Xn,On,e,n),Oe=h(()=>{const{common:{cubicBezierEaseInOut:t},self:{dotSize:r,dotColor:a,dotColorActive:l,dotColorFocus:u,dotLineWidth:s,dotLineWidthActive:p,arrowColor:m}}=_t.value;return{"--n-bezier":t,"--n-dot-color":a,"--n-dot-color-focus":u,"--n-dot-color-active":l,"--n-dot-size":r,"--n-dot-line-width":s,"--n-dot-line-width-active":p,"--n-arrow-color":m}}),X=o?Ft("carousel",void 0,Oe,e):void 0;return Object.assign(Object.assign({mergedClsPrefix:n,selfElRef:i,slidesElRef:f,slideVNodes:z,duplicatedable:b,userWantsControl:C,autoSlideSize:S,realIndex:D,slideStyles:De,translateStyle:xe,slidesControlListeners:At,handleTransitionEnd:Rt,handleResize:Pt,handleSlideResize:It,handleMouseenter:Dt,handleMouseleave:kt,isActive:xt,arrowSlotProps:Et,dotSlotProps:Tt},Nt),{cssVars:o?void 0:Oe,themeClass:X?.themeClass,onRender:X?.onRender})},render(){var e;const{mergedClsPrefix:n,showArrow:o,userWantsControl:i,slideStyles:f,dotType:g,dotPlacement:z,slidesControlListeners:y,transitionProps:P={},arrowSlotProps:x,dotSlotProps:v,$slots:{default:b,dots:C,arrow:$}}=this,M=b&&qt(b())||[];let S=Qn(M);return S.length||(S=M.map(R=>w(Zn,null,{default:()=>qe(R)}))),this.duplicatedable&&(S=Yn(S)),this.slideVNodes.value=S,this.autoSlideSize&&(S=S.map(R=>w(je,{onResize:this.handleSlideResize},{default:()=>R}))),(e=this.onRender)===null||e===void 0||e.call(this),w("div",Object.assign({ref:"selfElRef",class:[this.themeClass,`${n}-carousel`,this.direction==="vertical"&&`${n}-carousel--vertical`,this.showArrow&&`${n}-carousel--show-arrow`,`${n}-carousel--${z}`,`${n}-carousel--${this.direction}`,`${n}-carousel--${this.effect}`,i&&`${n}-carousel--usercontrol`],style:this.cssVars},y,{onMouseenter:this.handleMouseenter,onMouseleave:this.handleMouseleave}),w(je,{onResize:this.handleResize},{default:()=>w("div",{ref:"slidesElRef",class:`${n}-carousel__slides`,role:"listbox",style:this.translateStyle,onTransitionend:this.handleTransitionEnd},i?S.map((R,_)=>w("div",{style:f[_],key:_},Ut(w(Xt,Object.assign({},P),{default:()=>R}),[[Zt,this.isActive(_)]]))):S)}),this.showDots&&v.total>1&&Le(C,v,()=>[w(Bn,{key:g+z,total:v.total,currentIndex:v.currentIndex,dotType:g,trigger:this.trigger,keyboard:this.keyboard})]),o&&Le($,x,()=>[w(jn,null)]))}});function Qn(e){return e.reduce((n,o)=>(Wn(o)&&n.push(o),n),[])}export{nn as a,_n as i,Gn as n,ao as o,Zn as r,io as s,so as t};
