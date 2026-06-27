import{D as k,I as oo,z as c}from"./editor-BzczECHk.js";import{Bt as eo,ct as u,ft as x,g as ro,h as F,i as to,o as no,st as ao}from"./naive-ui-alert-47JY8xkM.js";import{C as w,T as lo,_ as r,b as l,c as io,d as so,g as co,v as a,w as bo,x as i}from"./naive-ui-affix-DrKOrtjc.js";import{z as go}from"./naive-ui-auto-complete-CCvmg59k.js";import{a as vo}from"./naive-ui-anchor-CMhXUotn.js";var po={paddingSmall:"12px 16px 12px",paddingMedium:"19px 24px 20px",paddingLarge:"23px 32px 24px",paddingHuge:"27px 40px 28px",titleFontSizeSmall:"16px",titleFontSizeMedium:"18px",titleFontSizeLarge:"18px",titleFontSizeHuge:"18px",closeIconSize:"18px",closeSize:"22px"};function fo(t){const{primaryColor:C,borderRadius:p,lineHeight:e,fontSize:v,cardColor:b,textColor2:f,textColor1:z,dividerColor:s,fontWeightStrong:d,closeIconColor:o,closeIconColorHover:n,closeIconColorPressed:g,closeColorHover:m,closeColorPressed:S,modalColor:y,boxShadow1:$,popoverColor:_,actionColor:h}=t;return Object.assign(Object.assign({},po),{lineHeight:e,color:b,colorModal:y,colorPopover:_,colorTarget:C,colorEmbedded:h,colorEmbeddedModal:h,colorEmbeddedPopover:h,textColor:f,titleTextColor:z,borderColor:s,actionColor:h,titleFontWeight:d,closeColorHover:m,closeColorPressed:S,closeBorderRadius:p,closeIconColor:o,closeIconColorHover:n,closeIconColorPressed:g,fontSizeSmall:v,fontSizeMedium:v,fontSizeLarge:v,fontSizeHuge:v,boxShadow:$,borderRadius:p})}var mo={name:"Card",common:to,self:fo},E=a("card-content",`
 flex: 1;
 min-width: 0;
 box-sizing: border-box;
 padding: 0 var(--n-padding-left) var(--n-padding-bottom) var(--n-padding-left);
 font-size: var(--n-font-size);
`),ho=r([a("card",`
 font-size: var(--n-font-size);
 line-height: var(--n-line-height);
 display: flex;
 flex-direction: column;
 width: 100%;
 box-sizing: border-box;
 position: relative;
 border-radius: var(--n-border-radius);
 background-color: var(--n-color);
 color: var(--n-text-color);
 word-break: break-word;
 transition: 
 color .3s var(--n-bezier),
 background-color .3s var(--n-bezier),
 box-shadow .3s var(--n-bezier),
 border-color .3s var(--n-bezier);
 `,[co({background:"var(--n-color-modal)"}),i("hoverable",[r("&:hover","box-shadow: var(--n-box-shadow);")]),i("content-segmented",[r(">",[a("card-content",`
 padding-top: var(--n-padding-bottom);
 `),l("content-scrollbar",[r(">",[a("scrollbar-container",[r(">",[a("card-content",`
 padding-top: var(--n-padding-bottom);
 `)])])])])])]),i("content-soft-segmented",[r(">",[a("card-content",`
 margin: 0 var(--n-padding-left);
 padding: var(--n-padding-bottom) 0;
 `),l("content-scrollbar",[r(">",[a("scrollbar-container",[r(">",[a("card-content",`
 margin: 0 var(--n-padding-left);
 padding: var(--n-padding-bottom) 0;
 `)])])])])])]),i("footer-segmented",[r(">",[l("footer",`
 padding-top: var(--n-padding-bottom);
 `)])]),i("footer-soft-segmented",[r(">",[l("footer",`
 padding: var(--n-padding-bottom) 0;
 margin: 0 var(--n-padding-left);
 `)])]),r(">",[a("card-header",`
 box-sizing: border-box;
 display: flex;
 align-items: center;
 font-size: var(--n-title-font-size);
 padding:
 var(--n-padding-top)
 var(--n-padding-left)
 var(--n-padding-bottom)
 var(--n-padding-left);
 `,[l("main",`
 font-weight: var(--n-title-font-weight);
 transition: color .3s var(--n-bezier);
 flex: 1;
 min-width: 0;
 color: var(--n-title-text-color);
 `),l("extra",`
 display: flex;
 align-items: center;
 font-size: var(--n-font-size);
 font-weight: 400;
 transition: color .3s var(--n-bezier);
 color: var(--n-text-color);
 `),l("close",`
 margin: 0 0 0 8px;
 transition:
 background-color .3s var(--n-bezier),
 color .3s var(--n-bezier);
 `)]),l("action",`
 box-sizing: border-box;
 transition:
 background-color .3s var(--n-bezier),
 border-color .3s var(--n-bezier);
 background-clip: padding-box;
 background-color: var(--n-action-color);
 `),E,a("card-content",[r("&:first-child",`
 padding-top: var(--n-padding-bottom);
 `)]),l("content-scrollbar",`
 display: flex;
 flex-direction: column;
 `,[r(">",[a("scrollbar-container",[r(">",[E])])]),r("&:first-child >",[a("scrollbar-container",[r(">",[a("card-content",`
 padding-top: var(--n-padding-bottom);
 `)])])])]),l("footer",`
 box-sizing: border-box;
 padding: 0 var(--n-padding-left) var(--n-padding-bottom) var(--n-padding-left);
 font-size: var(--n-font-size);
 `,[r("&:first-child",`
 padding-top: var(--n-padding-bottom);
 `)]),l("action",`
 background-color: var(--n-action-color);
 padding: var(--n-padding-bottom) var(--n-padding-left);
 border-bottom-left-radius: var(--n-border-radius);
 border-bottom-right-radius: var(--n-border-radius);
 `)]),a("card-cover",`
 overflow: hidden;
 width: 100%;
 border-radius: var(--n-border-radius) var(--n-border-radius) 0 0;
 `,[r("img",`
 display: block;
 width: 100%;
 `)]),i("bordered",`
 border: 1px solid var(--n-border-color);
 `,[r("&:target","border-color: var(--n-color-target);")]),i("action-segmented",[r(">",[l("action",[r("&:not(:first-child)",`
 border-top: 1px solid var(--n-border-color);
 `)])])]),i("content-segmented, content-soft-segmented",[r(">",[a("card-content",`
 transition: border-color 0.3s var(--n-bezier);
 `,[r("&:not(:first-child)",`
 border-top: 1px solid var(--n-border-color);
 `)]),l("content-scrollbar",`
 transition: border-color 0.3s var(--n-bezier);
 `,[r("&:not(:first-child)",`
 border-top: 1px solid var(--n-border-color);
 `)])])]),i("footer-segmented, footer-soft-segmented",[r(">",[l("footer",`
 transition: border-color 0.3s var(--n-bezier);
 `,[r("&:not(:first-child)",`
 border-top: 1px solid var(--n-border-color);
 `)])])]),i("embedded",`
 background-color: var(--n-color-embedded);
 `)]),bo(a("card",`
 background: var(--n-color-modal);
 `,[i("embedded",`
 background-color: var(--n-color-embedded-modal);
 `)])),lo(a("card",`
 background: var(--n-color-popover);
 `,[i("embedded",`
 background-color: var(--n-color-embedded-popover);
 `)]))]),P={title:[String,Function],contentClass:String,contentStyle:[Object,String],contentScrollable:Boolean,headerClass:String,headerStyle:[Object,String],headerExtraClass:String,headerExtraStyle:[Object,String],footerClass:String,footerStyle:[Object,String],embedded:Boolean,segmented:{type:[Boolean,Object],default:!1},size:String,bordered:{type:Boolean,default:!0},closable:Boolean,hoverable:Boolean,role:String,onClose:[Function,Array],tag:{type:String,default:"div"},cover:Function,content:[String,Function],footer:Function,action:Function,headerExtra:Function,closeFocusable:Boolean},$o=so(P),uo=Object.assign(Object.assign({},F.props),P),_o=oo({name:"Card",props:uo,slots:Object,setup(t){const C=()=>{const{onClose:n}=t;n&&go(n)},{inlineThemeDisabled:p,mergedClsPrefixRef:e,mergedRtlRef:v,mergedComponentPropsRef:b}=io(t),f=F("Card","-card",ho,mo,t,e),z=ro("Card",v,e),s=k(()=>{var n,g;return t.size||((g=(n=b?.value)===null||n===void 0?void 0:n.Card)===null||g===void 0?void 0:g.size)||"medium"}),d=k(()=>{const n=s.value,{self:{color:g,colorModal:m,colorTarget:S,textColor:y,titleTextColor:$,titleFontWeight:_,borderColor:h,actionColor:B,borderRadius:R,lineHeight:O,closeIconColor:M,closeIconColorHover:j,closeIconColorPressed:H,closeColorHover:I,closeColorPressed:T,closeBorderRadius:L,closeIconSize:V,closeSize:W,boxShadow:D,colorPopover:K,colorEmbedded:A,colorEmbeddedModal:N,colorEmbeddedPopover:q,[w("padding",n)]:G,[w("fontSize",n)]:J,[w("titleFontSize",n)]:Q},common:{cubicBezierEaseInOut:U}}=f.value,{top:X,left:Y,bottom:Z}=eo(G);return{"--n-bezier":U,"--n-border-radius":R,"--n-color":g,"--n-color-modal":m,"--n-color-popover":K,"--n-color-embedded":A,"--n-color-embedded-modal":N,"--n-color-embedded-popover":q,"--n-color-target":S,"--n-text-color":y,"--n-line-height":O,"--n-action-color":B,"--n-title-text-color":$,"--n-title-font-weight":_,"--n-close-icon-color":M,"--n-close-icon-color-hover":j,"--n-close-icon-color-pressed":H,"--n-close-color-hover":I,"--n-close-color-pressed":T,"--n-border-color":h,"--n-box-shadow":D,"--n-padding-top":X,"--n-padding-bottom":Z,"--n-padding-left":Y,"--n-font-size":J,"--n-title-font-size":Q,"--n-close-size":W,"--n-close-icon-size":V,"--n-close-border-radius":L}}),o=p?ao("card",k(()=>s.value[0]),d,t):void 0;return{rtlEnabled:z,mergedClsPrefix:e,mergedTheme:f,handleCloseClick:C,cssVars:p?void 0:d,themeClass:o?.themeClass,onRender:o?.onRender}},render(){const{segmented:t,bordered:C,hoverable:p,mergedClsPrefix:e,rtlEnabled:v,onRender:b,embedded:f,tag:z,$slots:s}=this;return b?.(),c(z,{class:[`${e}-card`,this.themeClass,f&&`${e}-card--embedded`,{[`${e}-card--rtl`]:v,[`${e}-card--content-scrollable`]:this.contentScrollable,[`${e}-card--content${typeof t!="boolean"&&t.content==="soft"?"-soft":""}-segmented`]:t===!0||t!==!1&&t.content,[`${e}-card--footer${typeof t!="boolean"&&t.footer==="soft"?"-soft":""}-segmented`]:t===!0||t!==!1&&t.footer,[`${e}-card--action-segmented`]:t===!0||t!==!1&&t.action,[`${e}-card--bordered`]:C,[`${e}-card--hoverable`]:p}],style:this.cssVars,role:this.role},x(s.cover,d=>{const o=this.cover?u([this.cover()]):d;return o&&c("div",{class:`${e}-card-cover`,role:"none"},o)}),x(s.header,d=>{const{title:o}=this,n=o?u(typeof o=="function"?[o()]:[o]):d;return n||this.closable?c("div",{class:[`${e}-card-header`,this.headerClass],style:this.headerStyle,role:"heading"},c("div",{class:`${e}-card-header__main`,role:"heading"},n),x(s["header-extra"],g=>{const m=this.headerExtra?u([this.headerExtra()]):g;return m&&c("div",{class:[`${e}-card-header__extra`,this.headerExtraClass],style:this.headerExtraStyle},m)}),this.closable&&c(no,{clsPrefix:e,class:`${e}-card-header__close`,onClick:this.handleCloseClick,focusable:this.closeFocusable,absolute:!0})):null}),x(s.default,d=>{const{content:o}=this,n=o?u(typeof o=="function"?[o()]:[o]):d;return n?this.contentScrollable?c(vo,{class:`${e}-card__content-scrollbar`,contentClass:[`${e}-card-content`,this.contentClass],contentStyle:this.contentStyle},n):c("div",{class:[`${e}-card-content`,this.contentClass],style:this.contentStyle,role:"none"},n):null}),x(s.footer,d=>{const o=this.footer?u([this.footer()]):d;return o&&c("div",{class:[`${e}-card__footer`,this.footerClass],style:this.footerStyle,role:"none"},o)}),x(s.action,d=>{const o=this.action?u([this.action()]):d;return o&&c("div",{class:`${e}-card__action`,role:"none"},o)}))}});export{mo as a,uo as i,$o as n,P as r,_o as t};
