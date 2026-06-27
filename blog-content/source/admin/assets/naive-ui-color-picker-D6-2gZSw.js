import{D as $,I as V,V as qe,W as st,bt as R,ct as Ee,et as ut,st as dt,ut as ct,wt as Se,z as l}from"./editor-BzczECHk.js";import{At as Ce,Dt as F,Et as Ue,Ft as N,It as Ae,Lt as $e,Mt as Ne,Nt as Re,Ot as _e,Pt as ve,St as P,Tt as O,Ut as ht,bt as re,gt as pt,h as Oe,i as ft,jt as T,kt as X,m as gt,pt as mt,st as vt,wt as le,xt as W}from"./naive-ui-alert-47JY8xkM.js";import{C as Ie,_ as x,b,c as Le,i as bt,p as xt,v as c,x as Fe}from"./naive-ui-affix-DrKOrtjc.js";import{A as kt,H as wt,J as yt,N as St,Y as Ct,Z as ze,at as Te,it as Ut,l as At,p as $t,q as Rt,s as _t,z as he}from"./naive-ui-auto-complete-CCvmg59k.js";import{S as He,b as oe,x as ae}from"./naive-ui-anchor-CMhXUotn.js";import{i as zt,t as pe}from"./naive-ui-button-C6uUobda.js";var Pt=c("input-group",`
 display: inline-flex;
 width: 100%;
 flex-wrap: nowrap;
 vertical-align: bottom;
`,[x(">",[c("input",[x("&:not(:last-child)",`
 border-top-right-radius: 0!important;
 border-bottom-right-radius: 0!important;
 `),x("&:not(:first-child)",`
 border-top-left-radius: 0!important;
 border-bottom-left-radius: 0!important;
 margin-left: -1px!important;
 `)]),c("button",[x("&:not(:last-child)",`
 border-top-right-radius: 0!important;
 border-bottom-right-radius: 0!important;
 `,[b("state-border, border",`
 border-top-right-radius: 0!important;
 border-bottom-right-radius: 0!important;
 `)]),x("&:not(:first-child)",`
 border-top-left-radius: 0!important;
 border-bottom-left-radius: 0!important;
 `,[b("state-border, border",`
 border-top-left-radius: 0!important;
 border-bottom-left-radius: 0!important;
 `)])]),x("*",[x("&:not(:last-child)",`
 border-top-right-radius: 0!important;
 border-bottom-right-radius: 0!important;
 `,[x(">",[c("input",`
 border-top-right-radius: 0!important;
 border-bottom-right-radius: 0!important;
 `),c("base-selection",[c("base-selection-label",`
 border-top-right-radius: 0!important;
 border-bottom-right-radius: 0!important;
 `),c("base-selection-tags",`
 border-top-right-radius: 0!important;
 border-bottom-right-radius: 0!important;
 `),b("box-shadow, border, state-border",`
 border-top-right-radius: 0!important;
 border-bottom-right-radius: 0!important;
 `)])])]),x("&:not(:first-child)",`
 margin-left: -1px!important;
 border-top-left-radius: 0!important;
 border-bottom-left-radius: 0!important;
 `,[x(">",[c("input",`
 border-top-left-radius: 0!important;
 border-bottom-left-radius: 0!important;
 `),c("base-selection",[c("base-selection-label",`
 border-top-left-radius: 0!important;
 border-bottom-left-radius: 0!important;
 `),c("base-selection-tags",`
 border-top-left-radius: 0!important;
 border-bottom-left-radius: 0!important;
 `),b("box-shadow, border, state-border",`
 border-top-left-radius: 0!important;
 border-bottom-left-radius: 0!important;
 `)])])])])])]),Vt={},Dt=V({name:"InputGroup",props:Vt,setup(e){const{mergedClsPrefixRef:t}=Le(e);return bt("-input-group",Pt,t),{mergedClsPrefix:t}},render(){const{mergedClsPrefix:e}=this;return l("div",{class:`${e}-input-group`},this.$slots)}});function Mt(e){const{fontSize:t,boxShadow2:i,popoverColor:o,textColor2:n,borderRadius:a,borderColor:s,heightSmall:u,heightMedium:f,heightLarge:w,fontSizeSmall:D,fontSizeMedium:H,fontSizeLarge:_,dividerColor:L}=e;return{panelFontSize:t,boxShadow:i,color:o,textColor:n,borderRadius:a,border:`1px solid ${s}`,heightSmall:u,heightMedium:f,heightLarge:w,fontSizeSmall:D,fontSizeMedium:H,fontSizeLarge:_,dividerColor:L}}var It=gt({name:"ColorPicker",common:ft,peers:{Input:At,Button:zt},self:Mt});function Ft(e,t){switch(e[0]){case"hex":return t?"#000000FF":"#000000";case"rgb":return t?"rgba(0, 0, 0, 1)":"rgb(0, 0, 0)";case"hsl":return t?"hsla(0, 0%, 0%, 1)":"hsl(0, 0%, 0%)";case"hsv":return t?"hsva(0, 0%, 0%, 1)":"hsv(0, 0%, 0%)"}return"#000000"}function se(e){return e===null?null:/^ *#/.test(e)?"hex":e.includes("rgb")?"rgb":e.includes("hsl")?"hsl":e.includes("hsv")?"hsv":null}function Tt(e,t=[255,255,255],i="AA"){const[o,n,a,s]=P(F(e));if(s===1){const w=fe([o,n,a]),D=fe(t);return(Math.max(w,D)+.05)/(Math.min(w,D)+.05)>=(i==="AA"?4.5:7)}const u=fe([Math.round(o*s+t[0]*(1-s)),Math.round(n*s+t[1]*(1-s)),Math.round(a*s+t[2]*(1-s))]),f=fe(t);return(Math.max(u,f)+.05)/(Math.min(u,f)+.05)>=(i==="AA"?4.5:7)}function fe(e){const[t,i,o]=e.map(n=>(n/=255,n<=.03928?n/12.92:Math.pow((n+.055)/1.055,2.4)));return .2126*t+.7152*i+.0722*o}function Ht(e){return e=Math.round(e),e>=360?359:e<0?0:e}function Bt(e){return e=Math.round(e*100)/100,e>1?1:e<0?0:e}var qt={rgb:{hex(e){return O(P(e))},hsl(e){const[t,i,o,n]=P(e);return F([...Ae(t,i,o),n])},hsv(e){const[t,i,o,n]=P(e);return X([...$e(t,i,o),n])}},hex:{rgb(e){return T(P(e))},hsl(e){const[t,i,o,n]=P(e);return F([...Ae(t,i,o),n])},hsv(e){const[t,i,o,n]=P(e);return X([...$e(t,i,o),n])}},hsl:{hex(e){const[t,i,o,n]=re(e);return O([...Re(t,i,o),n])},rgb(e){const[t,i,o,n]=re(e);return T([...Re(t,i,o),n])},hsv(e){const[t,i,o,n]=re(e);return X([...Ne(t,i,o),n])}},hsv:{hex(e){const[t,i,o,n]=W(e);return O([...N(t,i,o),n])},rgb(e){const[t,i,o,n]=W(e);return T([...N(t,i,o),n])},hsl(e){const[t,i,o,n]=W(e);return F([...ve(t,i,o),n])}}};function je(e,t,i){return i=i||se(e),i?i===t?e:qt[i][t](e):null}var ie="12px",Et=12,G="6px",Nt=V({name:"AlphaSlider",props:{clsPrefix:{type:String,required:!0},rgba:{type:Array,default:null},alpha:{type:Number,default:0},onUpdateAlpha:{type:Function,required:!0},onComplete:Function},setup(e){const t=R(null);function i(a){!t.value||!e.rgba||(ae("mousemove",document,o),ae("mouseup",document,n),o(a))}function o(a){const{value:s}=t;if(!s)return;const{width:u,left:f}=s.getBoundingClientRect(),w=(a.clientX-f)/(u-Et);e.onUpdateAlpha(Bt(w))}function n(){var a;oe("mousemove",document,o),oe("mouseup",document,n),(a=e.onComplete)===null||a===void 0||a.call(e)}return{railRef:t,railBackgroundImage:$(()=>{const{rgba:a}=e;return a?`linear-gradient(to right, rgba(${a[0]}, ${a[1]}, ${a[2]}, 0) 0%, rgba(${a[0]}, ${a[1]}, ${a[2]}, 1) 100%)`:""}),handleMouseDown:i}},render(){const{clsPrefix:e}=this;return l("div",{class:`${e}-color-picker-slider`,ref:"railRef",style:{height:ie,borderRadius:G},onMousedown:this.handleMouseDown},l("div",{style:{borderRadius:G,position:"absolute",left:0,right:0,top:0,bottom:0,overflow:"hidden"}},l("div",{class:`${e}-color-picker-checkboard`}),l("div",{class:`${e}-color-picker-slider__image`,style:{backgroundImage:this.railBackgroundImage}})),this.rgba&&l("div",{style:{position:"absolute",left:G,right:G,top:0,bottom:0}},l("div",{class:`${e}-color-picker-handle`,style:{left:`calc(${this.alpha*100}% - ${G})`,borderRadius:G,width:ie,height:ie}},l("div",{class:`${e}-color-picker-handle__fill`,style:{backgroundColor:T(this.rgba),borderRadius:G,width:ie,height:ie}}))))}}),Pe=xt("n-color-picker");function Ot(e){return/^\d{1,3}\.?\d*$/.test(e.trim())?Math.max(0,Math.min(Number.parseInt(e),255)):!1}function Lt(e){return/^\d{1,3}\.?\d*$/.test(e.trim())?Math.max(0,Math.min(Number.parseInt(e),360)):!1}function jt(e){return/^\d{1,3}\.?\d*$/.test(e.trim())?Math.max(0,Math.min(Number.parseInt(e),100)):!1}function Zt(e){const t=e.trim();return/^#[0-9a-fA-F]+$/.test(t)?[4,5,7,9].includes(t.length):!1}function Gt(e){return/^\d{1,3}\.?\d*%$/.test(e.trim())?Math.max(0,Math.min(Number.parseInt(e)/100,100)):!1}var Kt={paddingSmall:"0 4px"},Be=V({name:"ColorInputUnit",props:{label:{type:String,required:!0},value:{type:[Number,String],default:null},showAlpha:Boolean,onUpdateValue:{type:Function,required:!0}},setup(e){const t=R(""),{themeRef:i}=qe(Pe,null);Ee(()=>{t.value=o()});function o(){const{value:s}=e;if(s===null)return"";const{label:u}=e;return u==="HEX"?s:u==="A"?`${Math.floor(s*100)}%`:String(Math.floor(s))}function n(s){t.value=s}function a(s){let u,f;switch(e.label){case"HEX":f=Zt(s),f&&e.onUpdateValue(s),t.value=o();break;case"H":u=Lt(s),u===!1?t.value=o():e.onUpdateValue(u);break;case"S":case"L":case"V":u=jt(s),u===!1?t.value=o():e.onUpdateValue(u);break;case"A":u=Gt(s),u===!1?t.value=o():e.onUpdateValue(u);break;case"R":case"G":case"B":u=Ot(s),u===!1?t.value=o():e.onUpdateValue(u);break}}return{mergedTheme:i,inputValue:t,handleInputChange:a,handleInputUpdateValue:n}},render(){const{mergedTheme:e}=this;return l(_t,{size:"small",placeholder:this.label,theme:e.peers.Input,themeOverrides:e.peerOverrides.Input,builtinThemeOverrides:Kt,value:this.inputValue,onUpdateValue:this.handleInputUpdateValue,onChange:this.handleInputChange,style:this.label==="A"?"flex-grow: 1.25;":""})}}),Xt=V({name:"ColorInput",props:{clsPrefix:{type:String,required:!0},mode:{type:String,required:!0},modes:{type:Array,required:!0},showAlpha:{type:Boolean,required:!0},value:{type:String,default:null},valueArr:{type:Array,default:null},onUpdateValue:{type:Function,required:!0},onUpdateMode:{type:Function,required:!0}},setup(e){return{handleUnitUpdateValue(t,i){const{showAlpha:o}=e;if(e.mode==="hex"){e.onUpdateValue((o?O:le)(i));return}let n;switch(e.valueArr===null?n=[0,0,0,0]:n=Array.from(e.valueArr),e.mode){case"hsv":n[t]=i,e.onUpdateValue((o?X:_e)(n));break;case"rgb":n[t]=i,e.onUpdateValue((o?T:Ce)(n));break;case"hsl":n[t]=i,e.onUpdateValue((o?F:Ue)(n));break}}}},render(){const{clsPrefix:e,modes:t}=this;return l("div",{class:`${e}-color-picker-input`},l("div",{class:`${e}-color-picker-input__mode`,onClick:this.onUpdateMode,style:{cursor:t.length===1?"":"pointer"}},this.mode.toUpperCase()+(this.showAlpha?"A":"")),l(Dt,null,{default:()=>{const{mode:i,valueArr:o,showAlpha:n}=this;if(i==="hex"){let a=null;try{a=o===null?null:(n?O:le)(o)}catch{}return l(Be,{label:"HEX",showAlpha:n,value:a,onUpdateValue:s=>{this.handleUnitUpdateValue(0,s)}})}return(i+(n?"a":"")).split("").map((a,s)=>l(Be,{label:a.toUpperCase(),value:o===null?null:o[s],onUpdateValue:u=>{this.handleUnitUpdateValue(s,u)}}))}}))}});function Wt(e,t){if(t==="hsv"){const[i,o,n,a]=W(e);return T([...N(i,o,n),a])}return e}function Yt(e){const t=document.createElement("canvas").getContext("2d");return t?(t.fillStyle=e,t.fillStyle):"#000000"}var Jt=V({name:"ColorPickerSwatches",props:{clsPrefix:{type:String,required:!0},mode:{type:String,required:!0},swatches:{type:Array,required:!0},onUpdateColor:{type:Function,required:!0}},setup(e){const t=$(()=>e.swatches.map(a=>{const s=se(a);return{value:a,mode:s,legalValue:Wt(a,s)}}));function i(a){const{mode:s}=e;let{value:u,mode:f}=a;return f||(f="hex",/^[a-zA-Z]+$/.test(u)?u=Yt(u):(pt("color-picker",`color ${u} in swatches is invalid.`),u="#000000")),f===s?u:je(u,s,f)}function o(a){e.onUpdateColor(i(a))}function n(a,s){a.key==="Enter"&&o(s)}return{parsedSwatchesRef:t,handleSwatchSelect:o,handleSwatchKeyDown:n}},render(){const{clsPrefix:e}=this;return l("div",{class:`${e}-color-picker-swatches`},this.parsedSwatchesRef.map(t=>l("div",{class:`${e}-color-picker-swatch`,tabindex:0,onClick:()=>{this.handleSwatchSelect(t)},onKeydown:i=>{this.handleSwatchKeyDown(i,t)}},l("div",{class:`${e}-color-picker-swatch__fill`,style:{background:t.legalValue}}))))}}),Qt=V({name:"ColorPickerTrigger",slots:Object,props:{clsPrefix:{type:String,required:!0},value:{type:String,default:null},hsla:{type:Array,default:null},disabled:Boolean,onClick:Function},setup(e){const{colorPickerSlots:t,renderLabelRef:i}=qe(Pe,null);return()=>{const{hsla:o,value:n,clsPrefix:a,onClick:s,disabled:u}=e,f=t.label||i.value;return l("div",{class:[`${a}-color-picker`,u&&`${a}-color-picker--disabled`],onClick:u?void 0:s},l("div",{class:`${a}-color-picker__fill`},l("div",{class:`${a}-color-picker-checkboard`}),l("div",{style:{position:"absolute",left:0,right:0,top:0,bottom:0,backgroundColor:o?F(o):""}}),n&&o?l("div",{class:`${a}-color-picker__value`,style:{color:Tt(o)?"white":"black"}},f?f(n):n):null))}}}),er=V({name:"ColorPreview",props:{clsPrefix:{type:String,required:!0},mode:{type:String,required:!0},color:{type:String,default:null,validator:e=>{const t=se(e);return!!(!e||t&&t!=="hsv")}},onUpdateColor:{type:Function,required:!0}},setup(e){function t(i){var o;const n=i.target.value;(o=e.onUpdateColor)===null||o===void 0||o.call(e,je(n.toUpperCase(),e.mode,"hex")),i.stopPropagation()}return{handleChange:t}},render(){const{clsPrefix:e}=this;return l("div",{class:`${e}-color-picker-preview__preview`},l("span",{class:`${e}-color-picker-preview__fill`,style:{background:this.color||"#000000"}}),l("input",{class:`${e}-color-picker-preview__input`,type:"color",value:this.color,onChange:this.handleChange}))}}),te="12px",tr=12,K="6px",rr=6,or="linear-gradient(90deg,red,#ff0 16.66%,#0f0 33.33%,#0ff 50%,#00f 66.66%,#f0f 83.33%,red)",ar=V({name:"HueSlider",props:{clsPrefix:{type:String,required:!0},hue:{type:Number,required:!0},onUpdateHue:{type:Function,required:!0},onComplete:Function},setup(e){const t=R(null);function i(a){t.value&&(ae("mousemove",document,o),ae("mouseup",document,n),o(a))}function o(a){const{value:s}=t;if(!s)return;const{width:u,left:f}=s.getBoundingClientRect(),w=Ht((a.clientX-f-rr)/(u-tr)*360);e.onUpdateHue(w)}function n(){var a;oe("mousemove",document,o),oe("mouseup",document,n),(a=e.onComplete)===null||a===void 0||a.call(e)}return{railRef:t,handleMouseDown:i}},render(){const{clsPrefix:e}=this;return l("div",{class:`${e}-color-picker-slider`,style:{height:te,borderRadius:K}},l("div",{ref:"railRef",style:{boxShadow:"inset 0 0 2px 0 rgba(0, 0, 0, .24)",boxSizing:"border-box",backgroundImage:or,height:te,borderRadius:K,position:"relative"},onMousedown:this.handleMouseDown},l("div",{style:{position:"absolute",left:K,right:K,top:0,bottom:0}},l("div",{class:`${e}-color-picker-handle`,style:{left:`calc((${this.hue}%) / 359 * 100 - ${K})`,borderRadius:K,width:te,height:te}},l("div",{class:`${e}-color-picker-handle__fill`,style:{backgroundColor:`hsl(${this.hue}, 100%, 50%)`,borderRadius:K,width:te,height:te}})))))}}),ge="12px",me="6px",nr=V({name:"Pallete",props:{clsPrefix:{type:String,required:!0},rgba:{type:Array,default:null},displayedHue:{type:Number,required:!0},displayedSv:{type:Array,required:!0},onUpdateSV:{type:Function,required:!0},onComplete:Function},setup(e){const t=R(null);function i(a){t.value&&(ae("mousemove",document,o),ae("mouseup",document,n),o(a))}function o(a){const{value:s}=t;if(!s)return;const{width:u,height:f,left:w,bottom:D}=s.getBoundingClientRect(),H=(D-a.clientY)/f,_=(a.clientX-w)/u,L=100*(_>1?1:_<0?0:_),ue=100*(H>1?1:H<0?0:H);e.onUpdateSV(L,ue)}function n(){var a;oe("mousemove",document,o),oe("mouseup",document,n),(a=e.onComplete)===null||a===void 0||a.call(e)}return{palleteRef:t,handleColor:$(()=>{const{rgba:a}=e;return a?`rgb(${a[0]}, ${a[1]}, ${a[2]})`:""}),handleMouseDown:i}},render(){const{clsPrefix:e}=this;return l("div",{class:`${e}-color-picker-pallete`,onMousedown:this.handleMouseDown,ref:"palleteRef"},l("div",{class:`${e}-color-picker-pallete__layer`,style:{backgroundImage:`linear-gradient(90deg, white, hsl(${this.displayedHue}, 100%, 50%))`}}),l("div",{class:`${e}-color-picker-pallete__layer ${e}-color-picker-pallete__layer--shadowed`,style:{backgroundImage:"linear-gradient(180deg, rgba(0, 0, 0, 0%), rgba(0, 0, 0, 100%))"}}),this.rgba&&l("div",{class:`${e}-color-picker-handle`,style:{width:ge,height:ge,borderRadius:me,left:`calc(${this.displayedSv[0]}% - ${me})`,bottom:`calc(${this.displayedSv[1]}% - ${me})`}},l("div",{class:`${e}-color-picker-handle__fill`,style:{backgroundColor:this.handleColor,borderRadius:me,width:ge,height:ge}})))}}),ir=x([c("color-picker-panel",`
 margin: 4px 0;
 width: 240px;
 font-size: var(--n-panel-font-size);
 color: var(--n-text-color);
 background-color: var(--n-color);
 transition:
 box-shadow .3s var(--n-bezier),
 color .3s var(--n-bezier),
 background-color .3s var(--n-bezier);
 border-radius: var(--n-border-radius);
 box-shadow: var(--n-box-shadow);
 `,[$t(),c("input",`
 text-align: center;
 `)]),c("color-picker-checkboard",`
 background: white; 
 position: absolute;
 left: 0;
 right: 0;
 top: 0;
 bottom: 0;
 `,[x("&::after",`
 background-image: linear-gradient(45deg, #DDD 25%, #0000 25%), linear-gradient(-45deg, #DDD 25%, #0000 25%), linear-gradient(45deg, #0000 75%, #DDD 75%), linear-gradient(-45deg, #0000 75%, #DDD 75%);
 background-size: 12px 12px;
 background-position: 0 0, 0 6px, 6px -6px, -6px 0px;
 background-repeat: repeat;
 content: "";
 position: absolute;
 left: 0;
 right: 0;
 top: 0;
 bottom: 0;
 `)]),c("color-picker-slider",`
 margin-bottom: 8px;
 position: relative;
 box-sizing: border-box;
 `,[b("image",`
 position: absolute;
 left: 0;
 right: 0;
 top: 0;
 bottom: 0;
 `),x("&::after",`
 content: "";
 position: absolute;
 border-radius: inherit;
 left: 0;
 right: 0;
 top: 0;
 bottom: 0;
 box-shadow: inset 0 0 2px 0 rgba(0, 0, 0, .24);
 pointer-events: none;
 `)]),c("color-picker-handle",`
 z-index: 1;
 box-shadow: 0 0 2px 0 rgba(0, 0, 0, .45);
 position: absolute;
 background-color: white;
 overflow: hidden;
 `,[b("fill",`
 box-sizing: border-box;
 border: 2px solid white;
 `)]),c("color-picker-pallete",`
 height: 180px;
 position: relative;
 margin-bottom: 8px;
 cursor: crosshair;
 `,[b("layer",`
 position: absolute;
 left: 0;
 right: 0;
 top: 0;
 bottom: 0;
 `,[Fe("shadowed",`
 box-shadow: inset 0 0 2px 0 rgba(0, 0, 0, .24);
 `)])]),c("color-picker-preview",`
 display: flex;
 `,[b("sliders",`
 flex: 1 0 auto;
 `),b("preview",`
 position: relative;
 height: 30px;
 width: 30px;
 margin: 0 0 8px 6px;
 border-radius: 50%;
 box-shadow: rgba(0, 0, 0, .15) 0px 0px 0px 1px inset;
 overflow: hidden;
 `),b("fill",`
 display: block;
 width: 30px;
 height: 30px;
 `),b("input",`
 position: absolute;
 top: 0;
 left: 0;
 width: 30px;
 height: 30px;
 opacity: 0;
 z-index: 1;
 `)]),c("color-picker-input",`
 display: flex;
 align-items: center;
 `,[c("input",`
 flex-grow: 1;
 flex-basis: 0;
 `),b("mode",`
 width: 72px;
 text-align: center;
 `)]),c("color-picker-control",`
 padding: 12px;
 `),c("color-picker-action",`
 display: flex;
 margin-top: -4px;
 border-top: 1px solid var(--n-divider-color);
 padding: 8px 12px;
 justify-content: flex-end;
 `,[c("button","margin-left: 8px;")]),c("color-picker",`
 display: inline-block;
 box-sizing: border-box;
 height: var(--n-height);
 font-size: var(--n-font-size);
 width: 100%;
 position: relative;
 cursor: pointer;
 border: var(--n-border);
 border-radius: var(--n-border-radius);
 transition: border-color .3s var(--n-bezier);
 `,[Fe("disabled","cursor: not-allowed"),b("value",`
 white-space: nowrap;
 position: relative;
 `),b("fill",`
 border-radius: var(--n-border-radius);
 position: absolute;
 display: flex;
 align-items: center;
 justify-content: center;
 left: 4px;
 right: 4px;
 top: 4px;
 bottom: 4px;
 `),c("color-picker-checkboard",`
 border-radius: var(--n-border-radius);
 `,[x("&::after",`
 --n-block-size: calc((var(--n-height) - 8px) / 3);
 background-size: calc(var(--n-block-size) * 2) calc(var(--n-block-size) * 2);
 background-position: 0 0, 0 var(--n-block-size), var(--n-block-size) calc(-1 * var(--n-block-size)), calc(-1 * var(--n-block-size)) 0px; 
 `)])]),c("color-picker-swatches",`
 display: grid;
 grid-gap: 8px;
 flex-wrap: wrap;
 position: relative;
 grid-template-columns: repeat(auto-fill, 18px);
 margin-top: 10px;
 `,[c("color-picker-swatch",`
 width: 18px;
 height: 18px;
 background-image: linear-gradient(45deg, #DDD 25%, #0000 25%), linear-gradient(-45deg, #DDD 25%, #0000 25%), linear-gradient(45deg, #0000 75%, #DDD 75%), linear-gradient(-45deg, #0000 75%, #DDD 75%);
 background-size: 8px 8px;
 background-position: 0px 0, 0px 4px, 4px -4px, -4px 0px;
 background-repeat: repeat;
 `,[b("fill",`
 position: relative;
 width: 100%;
 height: 100%;
 border-radius: 3px;
 box-shadow: rgba(0, 0, 0, .15) 0px 0px 0px 1px inset;
 cursor: pointer;
 `),x("&:focus",`
 outline: none;
 `,[b("fill",[x("&::after",`
 position: absolute;
 top: 0;
 right: 0;
 bottom: 0;
 left: 0;
 background: inherit;
 filter: blur(2px);
 content: "";
 `)])])])])]),lr=Object.assign(Object.assign({},Oe.props),{value:String,show:{type:Boolean,default:void 0},defaultShow:Boolean,defaultValue:String,modes:{type:Array,default:()=>["rgb","hex","hsl"]},placement:{type:String,default:"bottom-start"},to:ze.propTo,showAlpha:{type:Boolean,default:!0},showPreview:Boolean,swatches:Array,disabled:{type:Boolean,default:void 0},actions:{type:Array,default:null},internalActions:Array,size:String,renderLabel:Function,onComplete:Function,onConfirm:Function,onClear:Function,"onUpdate:show":[Function,Array],onUpdateShow:[Function,Array],"onUpdate:value":[Function,Array],onUpdateValue:[Function,Array]}),fr=V({name:"ColorPicker",props:lr,slots:Object,setup(e,{slots:t}){let i=null;function o(r){i=r}let n=null;const{mergedClsPrefixRef:a,namespaceRef:s,inlineThemeDisabled:u,mergedComponentPropsRef:f}=Le(e),w=St(e,{mergedSize:r=>{var d,h;const{size:g}=e;if(g)return g;const{mergedSize:m}=r||{};if(m?.value)return m.value;const p=(h=(d=f?.value)===null||d===void 0?void 0:d.ColorPicker)===null||h===void 0?void 0:h.size;return p||"medium"}}),{mergedSizeRef:D,mergedDisabledRef:H}=w,{localeRef:_}=kt("global"),L=Oe("ColorPicker","-color-picker",ir,It,e,a);ut(Pe,{themeRef:L,renderLabelRef:Se(e,"renderLabel"),colorPickerSlots:t});const ue=R(e.defaultShow),Ve=Te(Se(e,"show"),ue);function de(r){const{onUpdateShow:d,"onUpdate:show":h}=e;d&&he(d,r),h&&he(h,r),ue.value=r}const{defaultValue:De}=e,Me=R(De===void 0?Ft(e.modes,e.showAlpha):De),y=Te(Se(e,"value"),Me),Y=R([y.value]),M=R(0),be=$(()=>se(y.value)),{modes:Ze}=e,z=R(se(y.value)||Ze[0]||"rgb");function Ge(){const{modes:r}=e,{value:d}=z,h=r.findIndex(g=>g===d);~h?z.value=r[(h+1)%r.length]:z.value="rgb"}let C,U,J,Q,B,q,E,A;const ne=$(()=>{const{value:r}=y;if(!r)return null;switch(be.value){case"hsv":return W(r);case"hsl":return[C,U,J,A]=re(r),[...Ne(C,U,J),A];case"rgb":case"hex":return[B,q,E,A]=P(r),[...$e(B,q,E),A]}}),j=$(()=>{const{value:r}=y;if(!r)return null;switch(be.value){case"rgb":case"hex":return P(r);case"hsv":return[C,U,Q,A]=W(r),[...N(C,U,Q),A];case"hsl":return[C,U,J,A]=re(r),[...Re(C,U,J),A]}}),xe=$(()=>{const{value:r}=y;if(!r)return null;switch(be.value){case"hsl":return re(r);case"hsv":return[C,U,Q,A]=W(r),[...ve(C,U,Q),A];case"rgb":case"hex":return[B,q,E,A]=P(r),[...Ae(B,q,E),A]}}),Ke=$(()=>{switch(z.value){case"rgb":case"hex":return j.value;case"hsv":return ne.value;case"hsl":return xe.value}}),ce=R(0),ke=R(1),we=R([0,0]);function Xe(r,d){const{value:h}=ne,g=ce.value,m=h?h[3]:1;we.value=[r,d];const{showAlpha:p}=e;switch(z.value){case"hsv":v((p?X:_e)([g,r,d,m]),"cursor");break;case"hsl":v((p?F:Ue)([...ve(g,r,d),m]),"cursor");break;case"rgb":v((p?T:Ce)([...N(g,r,d),m]),"cursor");break;case"hex":v((p?O:le)([...N(g,r,d),m]),"cursor");break}}function We(r){ce.value=r;const{value:d}=ne;if(!d)return;const[,h,g,m]=d,{showAlpha:p}=e;switch(z.value){case"hsv":v((p?X:_e)([r,h,g,m]),"cursor");break;case"rgb":v((p?T:Ce)([...N(r,h,g),m]),"cursor");break;case"hex":v((p?O:le)([...N(r,h,g),m]),"cursor");break;case"hsl":v((p?F:Ue)([...ve(r,h,g),m]),"cursor");break}}function Ye(r){switch(z.value){case"hsv":[C,U,Q]=ne.value,v(X([C,U,Q,r]),"cursor");break;case"rgb":[B,q,E]=j.value,v(T([B,q,E,r]),"cursor");break;case"hex":[B,q,E]=j.value,v(O([B,q,E,r]),"cursor");break;case"hsl":[C,U,J]=xe.value,v(F([C,U,J,r]),"cursor");break}ke.value=r}function v(r,d){d==="cursor"?n=r:n=null;const{nTriggerFormChange:h,nTriggerFormInput:g}=w,{onUpdateValue:m,"onUpdate:value":p}=e;m&&he(m,r),p&&he(p,r),h(),g(),Me.value=r}function Je(r){v(r,"input"),st(ee)}function ee(r=!0){const{value:d}=y;if(d){const{nTriggerFormChange:h,nTriggerFormInput:g}=w,{onComplete:m}=e;m&&m(d);const{value:p}=Y,{value:S}=M;r&&(p.splice(S+1,p.length,d),M.value=S+1),h(),g()}}function Qe(){const{value:r}=M;r-1<0||(v(Y.value[r-1],"input"),ee(!1),M.value=r-1)}function et(){const{value:r}=M;r<0||r+1>=Y.value.length||(v(Y.value[r+1],"input"),ee(!1),M.value=r+1)}function tt(){v(null,"input");const{onClear:r}=e;r&&r(),de(!1)}function rt(){const{value:r}=y,{onConfirm:d}=e;d&&d(r),de(!1)}const ot=$(()=>M.value>=1),at=$(()=>{const{value:r}=Y;return r.length>1&&M.value<r.length-1});dt(Ve,r=>{r||(Y.value=[y.value],M.value=0)}),Ee(()=>{if(!(n&&n===y.value)){const{value:r}=ne;r&&(ce.value=r[0],ke.value=r[3],we.value=[r[1],r[2]])}n=null});const ye=$(()=>{const{value:r}=D,{common:{cubicBezierEaseInOut:d},self:{textColor:h,color:g,panelFontSize:m,boxShadow:p,border:S,borderRadius:k,dividerColor:Z,[Ie("height",r)]:it,[Ie("fontSize",r)]:lt}}=L.value;return{"--n-bezier":d,"--n-text-color":h,"--n-color":g,"--n-panel-font-size":m,"--n-font-size":lt,"--n-box-shadow":p,"--n-border":S,"--n-border-radius":k,"--n-height":it,"--n-divider-color":Z}}),I=u?vt("color-picker",$(()=>D.value[0]),ye,e):void 0;function nt(){var r;const{value:d}=j,{value:h}=ce,{internalActions:g,modes:m,actions:p}=e,{value:S}=L,{value:k}=a;return l("div",{class:[`${k}-color-picker-panel`,I?.themeClass.value],onDragstart:Z=>{Z.preventDefault()},style:u?void 0:ye.value},l("div",{class:`${k}-color-picker-control`},l(nr,{clsPrefix:k,rgba:d,displayedHue:h,displayedSv:we.value,onUpdateSV:Xe,onComplete:ee}),l("div",{class:`${k}-color-picker-preview`},l("div",{class:`${k}-color-picker-preview__sliders`},l(ar,{clsPrefix:k,hue:h,onUpdateHue:We,onComplete:ee}),e.showAlpha?l(Nt,{clsPrefix:k,rgba:d,alpha:ke.value,onUpdateAlpha:Ye,onComplete:ee}):null),e.showPreview?l(er,{clsPrefix:k,mode:z.value,color:j.value&&le(j.value),onUpdateColor:Z=>{v(Z,"input")}}):null),l(Xt,{clsPrefix:k,showAlpha:e.showAlpha,mode:z.value,modes:m,onUpdateMode:Ge,value:y.value,valueArr:Ke.value,onUpdateValue:Je}),((r=e.swatches)===null||r===void 0?void 0:r.length)&&l(Jt,{clsPrefix:k,mode:z.value,swatches:e.swatches,onUpdateColor:Z=>{v(Z,"input")}})),p?.length?l("div",{class:`${k}-color-picker-action`},p.includes("confirm")&&l(pe,{size:"small",onClick:rt,theme:S.peers.Button,themeOverrides:S.peerOverrides.Button},{default:()=>_.value.confirm}),p.includes("clear")&&l(pe,{size:"small",onClick:tt,disabled:!y.value,theme:S.peers.Button,themeOverrides:S.peerOverrides.Button},{default:()=>_.value.clear})):null,t.action?l("div",{class:`${k}-color-picker-action`},{default:t.action}):g?l("div",{class:`${k}-color-picker-action`},g.includes("undo")&&l(pe,{size:"small",onClick:Qe,disabled:!ot.value,theme:S.peers.Button,themeOverrides:S.peerOverrides.Button},{default:()=>_.value.undo}),g.includes("redo")&&l(pe,{size:"small",onClick:et,disabled:!at.value,theme:S.peers.Button,themeOverrides:S.peerOverrides.Button},{default:()=>_.value.redo})):null)}return{mergedClsPrefix:a,namespace:s,hsla:xe,rgba:j,mergedShow:Ve,mergedDisabled:H,isMounted:Ut(),adjustedTo:ze(e),mergedValue:y,handleTriggerClick(){H.value||de(!0)},setTriggerRef:o,handleClickOutside(r){if(i instanceof Element){if(i.contains(He(r)))return}else if(i&&i.$el.contains(He(r)))return;de(!1)},renderPanel:nt,cssVars:u?void 0:ye,themeClass:I?.themeClass,onRender:I?.onRender}},render(){const{mergedClsPrefix:e,onRender:t}=this;return t?.(),l(Ct,null,{default:()=>[l(yt,null,{default:()=>mt(this.$slots.trigger,{value:this.mergedValue,onClick:this.handleTriggerClick,ref:this.setTriggerRef},i=>i||l(Qt,{clsPrefix:e,value:this.mergedValue,hsla:this.hsla,style:this.cssVars,ref:this.setTriggerRef,disabled:this.mergedDisabled,class:this.themeClass,onClick:this.mergedDisabled?void 0:this.handleTriggerClick}))}),l(wt,{placement:this.placement,show:this.mergedShow,containerClass:this.namespace,teleportDisabled:this.adjustedTo===ze.tdkey,to:this.adjustedTo},{default:()=>l(ht,{name:"fade-in-scale-up-transition",appear:this.isMounted},{default:()=>this.mergedShow?ct(this.renderPanel(),[[Rt,this.handleClickOutside,void 0,{capture:!0}]]):null})})]})}});export{Vt as i,lr as n,Dt as r,fr as t};
