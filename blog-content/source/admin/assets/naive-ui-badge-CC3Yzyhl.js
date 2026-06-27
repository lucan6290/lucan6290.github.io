import{D as g,I as C,W as z,X as W,bt as d,q as M,st as T,wt as S,z as l}from"./editor-BzczECHk.js";import{Ut as F,Wt as X,a as q,g as D,h as E,i as L,lt as U,st as V,ut as j}from"./naive-ui-alert-47JY8xkM.js";import{C as H,_ as s,b as Z,c as G,i as P,o as Y,v as c,x as m}from"./naive-ui-affix-DrKOrtjc.js";import{p as _}from"./naive-ui-auto-complete-CCvmg59k.js";import{d as K}from"./naive-ui-anchor-CMhXUotn.js";import{d as J}from"./naive-ui-avatar-Dkkn1t0c.js";var O=C({name:"SlotMachineNumber",props:{clsPrefix:{type:String,required:!0},value:{type:[Number,String],required:!0},oldOriginalNumber:{type:Number,default:void 0},newOriginalNumber:{type:Number,default:void 0}},setup(e){const a=d(null),i=d(e.value),o=d(e.value),t=d("up"),n=d(!1),b=g(()=>n.value?`${e.clsPrefix}-base-slot-machine-current-number--${t.value}-scroll`:null),x=g(()=>n.value?`${e.clsPrefix}-base-slot-machine-old-number--${t.value}-scroll`:null);T(S(e,"value"),(r,u)=>{i.value=u,o.value=r,z(N)});function N(){const r=e.newOriginalNumber,u=e.oldOriginalNumber;u===void 0||r===void 0||(r>u?$("up"):u>r&&$("down"))}function $(r){t.value=r,n.value=!1,z(()=>{var u;(u=a.value)===null||u===void 0||u.offsetWidth,n.value=!0})}return()=>{const{clsPrefix:r}=e;return l("span",{ref:a,class:`${r}-base-slot-machine-number`},i.value!==null?l("span",{class:[`${r}-base-slot-machine-old-number ${r}-base-slot-machine-old-number--top`,x.value]},i.value):null,l("span",{class:[`${r}-base-slot-machine-current-number`,b.value]},l("span",{ref:"numberWrapper",class:[`${r}-base-slot-machine-current-number__inner`,typeof e.value!="number"&&`${r}-base-slot-machine-current-number__inner--not-number`]},o.value)),i.value!==null?l("span",{class:[`${r}-base-slot-machine-old-number ${r}-base-slot-machine-old-number--bottom`,x.value]},i.value):null)}}}),{cubicBezierEaseInOut:h}=Y;function Q({duration:e=".2s",delay:a=".1s"}={}){return[s("&.fade-in-width-expand-transition-leave-from, &.fade-in-width-expand-transition-enter-to",{opacity:1}),s("&.fade-in-width-expand-transition-leave-to, &.fade-in-width-expand-transition-enter-from",`
 opacity: 0!important;
 margin-left: 0!important;
 margin-right: 0!important;
 `),s("&.fade-in-width-expand-transition-leave-active",`
 overflow: hidden;
 transition:
 opacity ${e} ${h},
 max-width ${e} ${h} ${a},
 margin-left ${e} ${h} ${a},
 margin-right ${e} ${h} ${a};
 `),s("&.fade-in-width-expand-transition-enter-active",`
 overflow: hidden;
 transition:
 opacity ${e} ${h} ${a},
 max-width ${e} ${h},
 margin-left ${e} ${h},
 margin-right ${e} ${h};
 `)]}var{cubicBezierEaseOut:w}=Y;function ee({duration:e=".2s"}={}){return[s("&.fade-up-width-expand-transition-leave-active",{transition:`
 opacity ${e} ${w},
 max-width ${e} ${w},
 transform ${e} ${w}
 `}),s("&.fade-up-width-expand-transition-enter-active",{transition:`
 opacity ${e} ${w},
 max-width ${e} ${w},
 transform ${e} ${w}
 `}),s("&.fade-up-width-expand-transition-enter-to",{opacity:1,transform:"translateX(0) translateY(0)"}),s("&.fade-up-width-expand-transition-enter-from",{maxWidth:"0 !important",opacity:0,transform:"translateY(60%)"}),s("&.fade-up-width-expand-transition-leave-from",{opacity:1,transform:"translateY(0)"}),s("&.fade-up-width-expand-transition-leave-to",{maxWidth:"0 !important",opacity:0,transform:"translateY(60%)"})]}var ae=s([s("@keyframes n-base-slot-machine-fade-up-in",`
 from {
 transform: translateY(60%);
 opacity: 0;
 }
 to {
 transform: translateY(0);
 opacity: 1;
 }
 `),s("@keyframes n-base-slot-machine-fade-down-in",`
 from {
 transform: translateY(-60%);
 opacity: 0;
 }
 to {
 transform: translateY(0);
 opacity: 1;
 }
 `),s("@keyframes n-base-slot-machine-fade-up-out",`
 from {
 transform: translateY(0%);
 opacity: 1;
 }
 to {
 transform: translateY(-60%);
 opacity: 0;
 }
 `),s("@keyframes n-base-slot-machine-fade-down-out",`
 from {
 transform: translateY(0%);
 opacity: 1;
 }
 to {
 transform: translateY(60%);
 opacity: 0;
 }
 `),c("base-slot-machine",`
 overflow: hidden;
 white-space: nowrap;
 display: inline-block;
 height: 18px;
 line-height: 18px;
 `,[c("base-slot-machine-number",`
 display: inline-block;
 position: relative;
 height: 18px;
 width: .6em;
 max-width: .6em;
 `,[ee({duration:".2s"}),Q({duration:".2s",delay:"0s"}),c("base-slot-machine-old-number",`
 display: inline-block;
 opacity: 0;
 position: absolute;
 left: 0;
 right: 0;
 `,[m("top",{transform:"translateY(-100%)"}),m("bottom",{transform:"translateY(100%)"}),m("down-scroll",{animation:"n-base-slot-machine-fade-down-out .2s cubic-bezier(0, 0, .2, 1)",animationIterationCount:1}),m("up-scroll",{animation:"n-base-slot-machine-fade-up-out .2s cubic-bezier(0, 0, .2, 1)",animationIterationCount:1})]),c("base-slot-machine-current-number",`
 display: inline-block;
 position: absolute;
 left: 0;
 top: 0;
 bottom: 0;
 right: 0;
 opacity: 1;
 transform: translateY(0);
 width: .6em;
 `,[m("down-scroll",{animation:"n-base-slot-machine-fade-down-in .2s cubic-bezier(0, 0, .2, 1)",animationIterationCount:1}),m("up-scroll",{animation:"n-base-slot-machine-fade-up-in .2s cubic-bezier(0, 0, .2, 1)",animationIterationCount:1}),Z("inner",`
 display: inline-block;
 position: absolute;
 right: 0;
 top: 0;
 width: .6em;
 `,[m("not-number",`
 right: unset;
 left: 0;
 `)])])])])]),te=C({name:"BaseSlotMachine",props:{clsPrefix:{type:String,required:!0},value:{type:[Number,String],default:0},max:{type:Number,default:void 0},appeared:{type:Boolean,required:!0}},setup(e){P("-base-slot-machine",ae,S(e,"clsPrefix"));const a=d(),i=d(),o=g(()=>{if(typeof e.value=="string")return[];if(e.value<1)return[0];const t=[];let n=e.value;for(e.max!==void 0&&(n=Math.min(e.max,n));n>=1;)t.push(n%10),n/=10,n=Math.floor(n);return t.reverse(),t});return T(S(e,"value"),(t,n)=>{typeof t=="string"?(i.value=void 0,a.value=void 0):typeof n=="string"?(i.value=t,a.value=void 0):(i.value=t,a.value=n)}),()=>{const{value:t,clsPrefix:n}=e;return typeof t=="number"?l("span",{class:`${n}-base-slot-machine`},l(X,{name:"fade-up-width-expand-transition",tag:"span"},{default:()=>o.value.map((b,x)=>l(O,{clsPrefix:n,key:o.value.length-x-1,oldOriginalNumber:a.value,newOriginalNumber:i.value,value:b}))}),l(q,{key:"+",width:!0},{default:()=>e.max!==void 0&&e.max<t?l(O,{clsPrefix:n,value:"+"}):null})):l("span",{class:`${n}-base-slot-machine`},t)}}}),ne=c("base-wave",`
 position: absolute;
 left: 0;
 right: 0;
 top: 0;
 bottom: 0;
 border-radius: inherit;
`),ie=C({name:"BaseWave",props:{clsPrefix:{type:String,required:!0}},setup(e){P("-base-wave",ne,S(e,"clsPrefix"));const a=d(null),i=d(!1);let o=null;return M(()=>{o!==null&&window.clearTimeout(o)}),{active:i,selfRef:a,play(){o!==null&&(window.clearTimeout(o),i.value=!1,o=null),z(()=>{var t;(t=a.value)===null||t===void 0||t.offsetHeight,i.value=!0,o=window.setTimeout(()=>{i.value=!1,o=null},1e3)})}}},render(){const{clsPrefix:e}=this;return l("div",{ref:"selfRef","aria-hidden":!0,class:[`${e}-base-wave`,this.active&&`${e}-base-wave--active`]})}});function re(e){const{errorColor:a,infoColor:i,successColor:o,warningColor:t,fontFamily:n}=e;return{color:a,colorInfo:i,colorSuccess:o,colorError:a,colorWarning:t,fontSize:"12px",fontFamily:n}}var oe={name:"Badge",common:L,self:re},se=s([s("@keyframes badge-wave-spread",{from:{boxShadow:"0 0 0.5px 0px var(--n-ripple-color)",opacity:.6},to:{boxShadow:"0 0 0.5px 4.5px var(--n-ripple-color)",opacity:0}}),c("badge",`
 display: inline-flex;
 position: relative;
 vertical-align: middle;
 font-family: var(--n-font-family);
 `,[m("as-is",[c("badge-sup",{position:"static",transform:"translateX(0)"},[_({transformOrigin:"left bottom",originalTransform:"translateX(0)"})])]),m("dot",[c("badge-sup",`
 height: 8px;
 width: 8px;
 padding: 0;
 min-width: 8px;
 left: 100%;
 bottom: calc(100% - 4px);
 `,[s("::before","border-radius: 4px;")])]),c("badge-sup",`
 background: var(--n-color);
 transition:
 background-color .3s var(--n-bezier),
 color .3s var(--n-bezier);
 color: #FFF;
 position: absolute;
 height: 18px;
 line-height: 18px;
 border-radius: 9px;
 padding: 0 6px;
 text-align: center;
 font-size: var(--n-font-size);
 transform: translateX(-50%);
 left: 100%;
 bottom: calc(100% - 9px);
 font-variant-numeric: tabular-nums;
 z-index: 2;
 display: flex;
 align-items: center;
 `,[_({transformOrigin:"left bottom",originalTransform:"translateX(-50%)"}),c("base-wave",{zIndex:1,animationDuration:"2s",animationIterationCount:"infinite",animationDelay:"1s",animationTimingFunction:"var(--n-ripple-bezier)",animationName:"badge-wave-spread"}),s("&::before",`
 opacity: 0;
 transform: scale(1);
 border-radius: 9px;
 content: "";
 position: absolute;
 left: 0;
 right: 0;
 top: 0;
 bottom: 0;
 `)])])]),le=Object.assign(Object.assign({},E.props),{value:[String,Number],max:Number,dot:Boolean,type:{type:String,default:"default"},show:{type:Boolean,default:!0},showZero:Boolean,processing:Boolean,color:String,offset:Array}),pe=C({name:"Badge",props:le,setup(e,{slots:a}){const{mergedClsPrefixRef:i,inlineThemeDisabled:o,mergedRtlRef:t}=G(e),n=E("Badge","-badge",se,oe,e,i),b=d(!1),x=()=>{b.value=!0},N=()=>{b.value=!1},$=g(()=>e.show&&(e.dot||e.value!==void 0&&!(!e.showZero&&Number(e.value)<=0)||!U(a.value)));W(()=>{$.value&&(b.value=!0)});const r=D("Badge",t,i),u=g(()=>{const{type:p,color:f}=e,{common:{cubicBezierEaseInOut:v,cubicBezierEaseOut:B},self:{[H("color",p)]:R,fontFamily:I,fontSize:A}}=n.value;return{"--n-font-size":A,"--n-font-family":I,"--n-color":f||R,"--n-ripple-color":f||R,"--n-bezier":v,"--n-ripple-bezier":B}}),y=o?V("badge",g(()=>{let p="";const{type:f,color:v}=e;return f&&(p+=f[0]),v&&(p+=J(v)),p}),u,e):void 0,k=g(()=>{const{offset:p}=e;if(!p)return;const[f,v]=p,B=typeof f=="number"?`${f}px`:f,R=typeof v=="number"?`${v}px`:v;return{transform:`translate(calc(${r?.value?"50%":"-50%"} + ${B}), ${R})`}});return{rtlEnabled:r,mergedClsPrefix:i,appeared:b,showBadge:$,handleAfterEnter:x,handleAfterLeave:N,cssVars:o?void 0:u,themeClass:y?.themeClass,onRender:y?.onRender,offsetStyle:k}},render(){var e;const{mergedClsPrefix:a,onRender:i,themeClass:o,$slots:t}=this;i?.();const n=(e=t.default)===null||e===void 0?void 0:e.call(t);return l("div",{class:[`${a}-badge`,this.rtlEnabled&&`${a}-badge--rtl`,o,{[`${a}-badge--dot`]:this.dot,[`${a}-badge--as-is`]:!n}],style:this.cssVars},n,l(F,{name:"fade-in-scale-up-transition",onAfterEnter:this.handleAfterEnter,onAfterLeave:this.handleAfterLeave},{default:()=>this.showBadge?l("sup",{class:`${a}-badge-sup`,title:K(this.value),style:this.offsetStyle},j(t.value,()=>[this.dot?null:l(te,{clsPrefix:a,appeared:this.appeared,max:this.max,value:this.value})]),this.processing?l(ie,{clsPrefix:a}):null):null}))}});export{Q as i,le as n,ie as r,pe as t};
