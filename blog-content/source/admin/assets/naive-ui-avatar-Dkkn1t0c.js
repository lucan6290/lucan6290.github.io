import{D as $,I as J,V as Y,X as xe,bt as E,ct as ke,et as ze,q as ye,st as Se,wt as Pe,z as P}from"./editor-BzczECHk.js";import{Bt as Ie,ft as U,g as Re,h as W,i as Q,o as Oe,st as Z,ut as $e,vt as h,yt as A}from"./naive-ui-alert-47JY8xkM.js";import{C as z,S as F,T as He,_ as M,b as O,c as ee,p as oe,v as K,w as _e,x as R}from"./naive-ui-affix-DrKOrtjc.js";import{X as Be,z as Me}from"./naive-ui-auto-complete-CCvmg59k.js";import{f as Ee}from"./naive-ui-anchor-CMhXUotn.js";function G(e){return e.replace(/#|\(|\)|,|\s|\./g,"_")}var Te={closeIconSizeTiny:"12px",closeIconSizeSmall:"12px",closeIconSizeMedium:"14px",closeIconSizeLarge:"14px",closeSizeTiny:"16px",closeSizeSmall:"16px",closeSizeMedium:"18px",closeSizeLarge:"18px",padding:"0 7px",closeMargin:"0 0 0 4px"};function je(e){const{textColor2:i,primaryColorHover:r,primaryColorPressed:v,primaryColor:n,infoColor:l,successColor:s,warningColor:c,errorColor:t,baseColor:g,borderColor:f,opacityDisabled:b,tagColor:C,closeIconColor:p,closeIconColorHover:x,closeIconColorPressed:a,borderRadiusSmall:u,fontSizeMini:y,fontSizeTiny:o,fontSizeSmall:d,fontSizeMedium:m,heightMini:S,heightTiny:k,heightSmall:H,heightMedium:I,closeColorHover:_,closeColorPressed:T,buttonColor2Hover:j,buttonColor2Pressed:w,fontWeightStrong:B}=e;return Object.assign(Object.assign({},Te),{closeBorderRadius:u,heightTiny:S,heightSmall:k,heightMedium:H,heightLarge:I,borderRadius:u,opacityDisabled:b,fontSizeTiny:y,fontSizeSmall:o,fontSizeMedium:d,fontSizeLarge:m,fontWeightStrong:B,textColorCheckable:i,textColorHoverCheckable:i,textColorPressedCheckable:i,textColorChecked:g,colorCheckable:"#0000",colorHoverCheckable:j,colorPressedCheckable:w,colorChecked:n,colorCheckedHover:r,colorCheckedPressed:v,border:`1px solid ${f}`,textColor:i,color:C,colorBordered:"rgb(250, 250, 252)",closeIconColor:p,closeIconColorHover:x,closeIconColorPressed:a,closeColorHover:_,closeColorPressed:T,borderPrimary:`1px solid ${h(n,{alpha:.3})}`,textColorPrimary:n,colorPrimary:h(n,{alpha:.12}),colorBorderedPrimary:h(n,{alpha:.1}),closeIconColorPrimary:n,closeIconColorHoverPrimary:n,closeIconColorPressedPrimary:n,closeColorHoverPrimary:h(n,{alpha:.12}),closeColorPressedPrimary:h(n,{alpha:.18}),borderInfo:`1px solid ${h(l,{alpha:.3})}`,textColorInfo:l,colorInfo:h(l,{alpha:.12}),colorBorderedInfo:h(l,{alpha:.1}),closeIconColorInfo:l,closeIconColorHoverInfo:l,closeIconColorPressedInfo:l,closeColorHoverInfo:h(l,{alpha:.12}),closeColorPressedInfo:h(l,{alpha:.18}),borderSuccess:`1px solid ${h(s,{alpha:.3})}`,textColorSuccess:s,colorSuccess:h(s,{alpha:.12}),colorBorderedSuccess:h(s,{alpha:.1}),closeIconColorSuccess:s,closeIconColorHoverSuccess:s,closeIconColorPressedSuccess:s,closeColorHoverSuccess:h(s,{alpha:.12}),closeColorPressedSuccess:h(s,{alpha:.18}),borderWarning:`1px solid ${h(c,{alpha:.35})}`,textColorWarning:c,colorWarning:h(c,{alpha:.15}),colorBorderedWarning:h(c,{alpha:.12}),closeIconColorWarning:c,closeIconColorHoverWarning:c,closeIconColorPressedWarning:c,closeColorHoverWarning:h(c,{alpha:.12}),closeColorPressedWarning:h(c,{alpha:.18}),borderError:`1px solid ${h(t,{alpha:.23})}`,textColorError:t,colorError:h(t,{alpha:.1}),colorBorderedError:h(t,{alpha:.08}),closeIconColorError:t,closeIconColorHoverError:t,closeIconColorPressedError:t,closeColorHoverError:h(t,{alpha:.12}),closeColorPressedError:h(t,{alpha:.18})})}var we={name:"Tag",common:Q,self:je},Le={color:Object,type:{type:String,default:"default"},round:Boolean,size:String,closable:Boolean,disabled:{type:Boolean,default:void 0}},Fe=K("tag",`
 --n-close-margin: var(--n-close-margin-top) var(--n-close-margin-right) var(--n-close-margin-bottom) var(--n-close-margin-left);
 white-space: nowrap;
 position: relative;
 box-sizing: border-box;
 cursor: default;
 display: inline-flex;
 align-items: center;
 flex-wrap: nowrap;
 padding: var(--n-padding);
 border-radius: var(--n-border-radius);
 color: var(--n-text-color);
 background-color: var(--n-color);
 transition: 
 border-color .3s var(--n-bezier),
 background-color .3s var(--n-bezier),
 color .3s var(--n-bezier),
 box-shadow .3s var(--n-bezier),
 opacity .3s var(--n-bezier);
 line-height: 1;
 height: var(--n-height);
 font-size: var(--n-font-size);
`,[R("strong",`
 font-weight: var(--n-font-weight-strong);
 `),O("border",`
 pointer-events: none;
 position: absolute;
 left: 0;
 right: 0;
 top: 0;
 bottom: 0;
 border-radius: inherit;
 border: var(--n-border);
 transition: border-color .3s var(--n-bezier);
 `),O("icon",`
 display: flex;
 margin: 0 4px 0 0;
 color: var(--n-text-color);
 transition: color .3s var(--n-bezier);
 font-size: var(--n-avatar-size-override);
 `),O("avatar",`
 display: flex;
 margin: 0 6px 0 0;
 `),O("close",`
 margin: var(--n-close-margin);
 transition:
 background-color .3s var(--n-bezier),
 color .3s var(--n-bezier);
 `),R("round",`
 padding: 0 calc(var(--n-height) / 3);
 border-radius: calc(var(--n-height) / 2);
 `,[O("icon",`
 margin: 0 4px 0 calc((var(--n-height) - 8px) / -2);
 `),O("avatar",`
 margin: 0 6px 0 calc((var(--n-height) - 8px) / -2);
 `),R("closable",`
 padding: 0 calc(var(--n-height) / 4) 0 calc(var(--n-height) / 3);
 `)]),R("icon, avatar",[R("round",`
 padding: 0 calc(var(--n-height) / 3) 0 calc(var(--n-height) / 2);
 `)]),R("disabled",`
 cursor: not-allowed !important;
 opacity: var(--n-opacity-disabled);
 `),R("checkable",`
 cursor: pointer;
 box-shadow: none;
 color: var(--n-text-color-checkable);
 background-color: var(--n-color-checkable);
 `,[F("disabled",[M("&:hover","background-color: var(--n-color-hover-checkable);",[F("checked","color: var(--n-text-color-hover-checkable);")]),M("&:active","background-color: var(--n-color-pressed-checkable);",[F("checked","color: var(--n-text-color-pressed-checkable);")])]),R("checked",`
 color: var(--n-text-color-checked);
 background-color: var(--n-color-checked);
 `,[F("disabled",[M("&:hover","background-color: var(--n-color-checked-hover);"),M("&:active","background-color: var(--n-color-checked-pressed);")])])])]),We=Object.assign(Object.assign(Object.assign({},W.props),Le),{bordered:{type:Boolean,default:void 0},checked:Boolean,checkable:Boolean,strong:Boolean,triggerClickOnClose:Boolean,onClose:[Array,Function],onMouseenter:Function,onMouseleave:Function,"onUpdate:checked":Function,onUpdateChecked:Function,internalCloseFocusable:{type:Boolean,default:!0},internalCloseIsButtonTag:{type:Boolean,default:!0},onCheckedChange:Function}),re=oe("n-tag"),eo=J({name:"Tag",props:We,slots:Object,setup(e){const i=E(null),{mergedBorderedRef:r,mergedClsPrefixRef:v,inlineThemeDisabled:n,mergedRtlRef:l,mergedComponentPropsRef:s}=ee(e),c=$(()=>{var a,u;return e.size||((u=(a=s?.value)===null||a===void 0?void 0:a.Tag)===null||u===void 0?void 0:u.size)||"medium"}),t=W("Tag","-tag",Fe,we,e,v);ze(re,{roundRef:Pe(e,"round")});function g(){if(!e.disabled&&e.checkable){const{checked:a,onCheckedChange:u,onUpdateChecked:y,"onUpdate:checked":o}=e;y&&y(!a),o&&o(!a),u&&u(!a)}}function f(a){if(e.triggerClickOnClose||a.stopPropagation(),!e.disabled){const{onClose:u}=e;u&&Me(u,a)}}const b={setTextContent(a){const{value:u}=i;u&&(u.textContent=a)}},C=Re("Tag",l,v),p=$(()=>{const{type:a,color:{color:u,textColor:y}={}}=e,o=c.value,{common:{cubicBezierEaseInOut:d},self:{padding:m,closeMargin:S,borderRadius:k,opacityDisabled:H,textColorCheckable:I,textColorHoverCheckable:_,textColorPressedCheckable:T,textColorChecked:j,colorCheckable:w,colorHoverCheckable:B,colorPressedCheckable:ae,colorChecked:te,colorCheckedHover:le,colorCheckedPressed:ne,closeBorderRadius:se,fontWeightStrong:ce,[z("colorBordered",a)]:ie,[z("closeSize",o)]:de,[z("closeIconSize",o)]:he,[z("fontSize",o)]:ve,[z("height",o)]:X,[z("color",a)]:ue,[z("textColor",a)]:ge,[z("border",a)]:be,[z("closeIconColor",a)]:q,[z("closeIconColorHover",a)]:fe,[z("closeIconColorPressed",a)]:me,[z("closeColorHover",a)]:Ce,[z("closeColorPressed",a)]:pe}}=t.value,L=Ie(S);return{"--n-font-weight-strong":ce,"--n-avatar-size-override":`calc(${X} - 8px)`,"--n-bezier":d,"--n-border-radius":k,"--n-border":be,"--n-close-icon-size":he,"--n-close-color-pressed":pe,"--n-close-color-hover":Ce,"--n-close-border-radius":se,"--n-close-icon-color":q,"--n-close-icon-color-hover":fe,"--n-close-icon-color-pressed":me,"--n-close-icon-color-disabled":q,"--n-close-margin-top":L.top,"--n-close-margin-right":L.right,"--n-close-margin-bottom":L.bottom,"--n-close-margin-left":L.left,"--n-close-size":de,"--n-color":u||(r.value?ie:ue),"--n-color-checkable":w,"--n-color-checked":te,"--n-color-checked-hover":le,"--n-color-checked-pressed":ne,"--n-color-hover-checkable":B,"--n-color-pressed-checkable":ae,"--n-font-size":ve,"--n-height":X,"--n-opacity-disabled":H,"--n-padding":m,"--n-text-color":y||ge,"--n-text-color-checkable":I,"--n-text-color-checked":j,"--n-text-color-hover-checkable":_,"--n-text-color-pressed-checkable":T}}),x=n?Z("tag",$(()=>{let a="";const{type:u,color:{color:y,textColor:o}={}}=e;return a+=u[0],a+=c.value[0],y&&(a+=`a${G(y)}`),o&&(a+=`b${G(o)}`),r.value&&(a+="c"),a}),p,e):void 0;return Object.assign(Object.assign({},b),{rtlEnabled:C,mergedClsPrefix:v,contentRef:i,mergedBordered:r,handleClick:g,handleCloseClick:f,cssVars:n?void 0:p,themeClass:x?.themeClass,onRender:x?.onRender})},render(){var e,i;const{mergedClsPrefix:r,rtlEnabled:v,closable:n,color:{borderColor:l}={},round:s,onRender:c,$slots:t}=this;c?.();const g=U(t.avatar,b=>b&&P("div",{class:`${r}-tag__avatar`},b)),f=U(t.icon,b=>b&&P("div",{class:`${r}-tag__icon`},b));return P("div",{class:[`${r}-tag`,this.themeClass,{[`${r}-tag--rtl`]:v,[`${r}-tag--strong`]:this.strong,[`${r}-tag--disabled`]:this.disabled,[`${r}-tag--checkable`]:this.checkable,[`${r}-tag--checked`]:this.checkable&&this.checked,[`${r}-tag--round`]:s,[`${r}-tag--avatar`]:g,[`${r}-tag--icon`]:f,[`${r}-tag--closable`]:n}],style:this.cssVars,onClick:this.handleClick,onMouseenter:this.onMouseenter,onMouseleave:this.onMouseleave},f||g,P("span",{class:`${r}-tag__content`,ref:"contentRef"},(i=(e=this.$slots).default)===null||i===void 0?void 0:i.call(e)),!this.checkable&&n?P(Oe,{clsPrefix:r,class:`${r}-tag__close`,disabled:this.disabled,onClick:this.handleCloseClick,focusable:this.internalCloseFocusable,round:s,isButtonTag:this.internalCloseIsButtonTag,absolute:!0}):null,!this.checkable&&this.mergedBordered?P("div",{class:`${r}-tag__border`,style:{borderColor:l}}):null)}}),Ae=Be&&"loading"in document.createElement("img");function Ve(e={}){var i;const{root:r=null}=e;return{hash:`${e.rootMargin||"0px 0px 0px 0px"}-${Array.isArray(e.threshold)?e.threshold.join(","):(i=e.threshold)!==null&&i!==void 0?i:"0"}`,options:Object.assign(Object.assign({},e),{root:(typeof r=="string"?document.querySelector(r):r)||document.documentElement})}}var V=new WeakMap,N=new WeakMap,D=new WeakMap,Ne=(e,i,r)=>{if(!e)return()=>{};const v=Ve(i),{root:n}=v.options;let l;const s=V.get(n);s?l=s:(l=new Map,V.set(n,l));let c,t;l.has(v.hash)?(t=l.get(v.hash),t[1].has(e)||(c=t[0],t[1].add(e),c.observe(e))):(c=new IntersectionObserver(b=>{b.forEach(C=>{if(C.isIntersecting){const p=N.get(C.target),x=D.get(C.target);p&&p(),x&&(x.value=!0)}})},v.options),c.observe(e),t=[c,new Set([e])],l.set(v.hash,t));let g=!1;const f=()=>{g||(N.delete(e),D.delete(e),g=!0,t[1].has(e)&&(t[0].unobserve(e),t[1].delete(e)),t[1].size<=0&&l.delete(v.hash),l.size||V.delete(n))};return N.set(e,f),D.set(e,r),f};function De(e){const{borderRadius:i,avatarColor:r,cardColor:v,fontSize:n,heightTiny:l,heightSmall:s,heightMedium:c,heightLarge:t,heightHuge:g,modalColor:f,popoverColor:b}=e;return{borderRadius:i,fontSize:n,border:`2px solid ${v}`,heightTiny:l,heightSmall:s,heightMedium:c,heightLarge:t,heightHuge:g,color:A(v,r),colorModal:A(f,r),colorPopover:A(b,r)}}var Ue={name:"Avatar",common:Q,self:De},Ke=oe("n-avatar-group"),Ge=K("avatar",`
 width: var(--n-merged-size);
 height: var(--n-merged-size);
 color: #FFF;
 font-size: var(--n-font-size);
 display: inline-flex;
 position: relative;
 overflow: hidden;
 text-align: center;
 border: var(--n-border);
 border-radius: var(--n-border-radius);
 --n-merged-color: var(--n-color);
 background-color: var(--n-merged-color);
 transition:
 border-color .3s var(--n-bezier),
 background-color .3s var(--n-bezier),
 color .3s var(--n-bezier);
`,[_e(M("&","--n-merged-color: var(--n-color-modal);")),He(M("&","--n-merged-color: var(--n-color-popover);")),M("img",`
 width: 100%;
 height: 100%;
 `),O("text",`
 white-space: nowrap;
 display: inline-block;
 position: absolute;
 left: 50%;
 top: 50%;
 `),K("icon",`
 vertical-align: bottom;
 font-size: calc(var(--n-merged-size) - 6px);
 `),O("text","line-height: 1.25")]),Xe=Object.assign(Object.assign({},W.props),{size:[String,Number],src:String,circle:{type:Boolean,default:void 0},objectFit:String,round:{type:Boolean,default:void 0},bordered:{type:Boolean,default:void 0},onError:Function,fallbackSrc:String,intersectionObserverOptions:Object,lazy:Boolean,onLoad:Function,renderPlaceholder:Function,renderFallback:Function,imgProps:Object,color:String}),oo=J({name:"Avatar",props:Xe,slots:Object,setup(e){const{mergedClsPrefixRef:i,inlineThemeDisabled:r}=ee(e),v=E(!1);let n=null;const l=E(null),s=E(null),c=()=>{const{value:o}=l;if(o&&(n===null||n!==o.innerHTML)){n=o.innerHTML;const{value:d}=s;if(d){const{offsetWidth:m,offsetHeight:S}=d,{offsetWidth:k,offsetHeight:H}=o,I=.9,_=Math.min(m/k*I,S/H*I,1);o.style.transform=`translateX(-50%) translateY(-50%) scale(${_})`}}},t=Y(Ke,null),g=$(()=>{const{size:o}=e;if(o)return o;const{size:d}=t||{};return d||"medium"}),f=W("Avatar","-avatar",Ge,Ue,e,i),b=Y(re,null),C=$(()=>{if(t)return!0;const{round:o,circle:d}=e;return o!==void 0||d!==void 0?o||d:b?b.roundRef.value:!1}),p=$(()=>t?!0:e.bordered||!1),x=$(()=>{const o=g.value,d=C.value,m=p.value,{color:S}=e,{self:{borderRadius:k,fontSize:H,color:I,border:_,colorModal:T,colorPopover:j},common:{cubicBezierEaseInOut:w}}=f.value;let B;return typeof o=="number"?B=`${o}px`:B=f.value.self[z("height",o)],{"--n-font-size":H,"--n-border":m?_:"none","--n-border-radius":d?"50%":k,"--n-color":S||I,"--n-color-modal":S||T,"--n-color-popover":S||j,"--n-bezier":w,"--n-merged-size":`var(--n-avatar-size-override, ${B})`}}),a=r?Z("avatar",$(()=>{const o=g.value,d=C.value,m=p.value,{color:S}=e;let k="";return o&&(typeof o=="number"?k+=`a${o}`:k+=o[0]),d&&(k+="b"),m&&(k+="c"),S&&(k+=G(S)),k}),x,e):void 0,u=E(!e.lazy);xe(()=>{if(e.lazy&&e.intersectionObserverOptions){let o;const d=ke(()=>{o?.(),o=void 0,e.lazy&&(o=Ne(s.value,e.intersectionObserverOptions,u))});ye(()=>{d(),o?.()})}}),Se(()=>{var o;return e.src||((o=e.imgProps)===null||o===void 0?void 0:o.src)},()=>{v.value=!1});const y=E(!e.lazy);return{textRef:l,selfRef:s,mergedRoundRef:C,mergedClsPrefix:i,fitTextTransform:c,cssVars:r?void 0:x,themeClass:a?.themeClass,onRender:a?.onRender,hasLoadError:v,shouldStartLoading:u,loaded:y,mergedOnError:o=>{if(!u.value)return;v.value=!0;const{onError:d,imgProps:{onError:m}={}}=e;d?.(o),m?.(o)},mergedOnLoad:o=>{const{onLoad:d,imgProps:{onLoad:m}={}}=e;d?.(o),m?.(o),y.value=!0}}},render(){var e,i;const{$slots:r,src:v,mergedClsPrefix:n,lazy:l,onRender:s,loaded:c,hasLoadError:t,imgProps:g={}}=this;s?.();let f;const b=!c&&!t&&(this.renderPlaceholder?this.renderPlaceholder():(i=(e=this.$slots).placeholder)===null||i===void 0?void 0:i.call(e));return this.hasLoadError?f=this.renderFallback?this.renderFallback():$e(r.fallback,()=>[P("img",{src:this.fallbackSrc,style:{objectFit:this.objectFit}})]):f=U(r.default,C=>{if(C)return P(Ee,{onResize:this.fitTextTransform},{default:()=>P("span",{ref:"textRef",class:`${n}-avatar__text`},C)});if(v||g.src){const p=this.src||g.src;return P("img",Object.assign(Object.assign({},g),{loading:Ae&&!this.intersectionObserverOptions&&l?"lazy":"eager",src:l&&this.intersectionObserverOptions?this.shouldStartLoading?p:void 0:p,"data-image-src":p,onLoad:this.mergedOnLoad,onError:this.mergedOnError,style:[g.style||"",{objectFit:this.objectFit},b?{height:"0",width:"0",visibility:"hidden",position:"absolute"}:""]}))}}),P("span",{ref:"selfRef",class:[`${n}-avatar`,this.themeClass],style:this.cssVars},f,l&&b)}});export{Ne as a,We as c,G as d,Ue as i,Le as l,Xe as n,Ae as o,Ke as r,eo as s,oo as t,we as u};
