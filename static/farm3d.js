
/*
 BUMI SHIFT — Interactive 3D Farm
 HANOVA | Sarawak

 Works with the existing index.html.
 No backend changes required.

 This is a 3D scenario viewer, not a
 measured reconstruction of an actual farm.
*/

import * as THREE from
 "https://cdn.jsdelivr.net/npm/three@0.160.1/build/three.module.js";

import { OrbitControls } from
 "https://cdn.jsdelivr.net/npm/three@0.160.1/examples/jsm/controls/OrbitControls.js";

const originalFarm = document.querySelector(".farm");

if (!originalFarm) {
 throw new Error("BUMI SHIFT farm container not found");
}

// Replace only the old flat farm illustration.
const viewer = document.createElement("div");
viewer.id = "farm3d";
viewer.style.cssText = `
 height:430px;
 width:100%;
 position:relative;
 overflow:hidden;
 border-radius:17px;
 background:linear-gradient(#9fd4ef,#e2f4ed);
 touch-action:none;
`;

originalFarm.replaceWith(viewer);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0xaad7ec);
scene.fog = new THREE.Fog(0xaad7ec, 35, 75);

const camera = new THREE.PerspectiveCamera(
 45, 1, 0.1, 100
);
camera.position.set(16, 15, 19);

const renderer = new THREE.WebGLRenderer({
 antialias:true
});
renderer.setPixelRatio(
 Math.min(window.devicePixelRatio, 2)
);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.3;

viewer.appendChild(renderer.domElement);

const controls = new OrbitControls(
 camera, renderer.domElement
);
controls.enableDamping = true;
controls.target.set(0, 0, 0);
controls.minDistance = 6;
controls.maxDistance = 38;
controls.maxPolarAngle = Math.PI * 0.49;

scene.add(new THREE.HemisphereLight(
 0xffffff, 0x55785a, 2.2
));

const sun = new THREE.DirectionalLight(
 0xfff1d5, 2.7
);
sun.position.set(-8, 18, 12);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
sun.shadow.camera.left = -20;
sun.shadow.camera.right = 20;
sun.shadow.camera.top = 20;
sun.shadow.camera.bottom = -20;
scene.add(sun);

function material(color) {
 return new THREE.MeshStandardMaterial({
  color, roughness:0.8
 });
}

const M = {
 grass:material("#69a45d"),
 soil:material("#845e40"),
 darkSoil:material("#68462f"),
 path:material("#d8b987"),
 rice:material("#4b9c47"),
 riceLight:material("#8ccf5c"),
 grain:material("#e8cb68"),
 maize:material("#378a46"),
 corn:material("#f4cb57"),
 legume:material("#37a55d"),
 leaf:material("#65bb62"),
 trunk:material("#78513a"),
 tree:material("#327b49"),
 roof:material("#ae6746"),
 wall:material("#ead7b4"),
 water:new THREE.MeshStandardMaterial({
  color:"#48bce0",
  roughness:0.2,
  metalness:0.1,
  transparent:true,
  opacity:0.85
 })
};

function add(geometry, mat, parent=scene) {
 const object = new THREE.Mesh(geometry,mat);
 object.castShadow = true;
 object.receiveShadow = true;
 parent.add(object);
 return object;
}

function box(w,h,d,mat,x,y,z,parent=scene) {
 const obj=add(
  new THREE.BoxGeometry(w,h,d),mat,parent
 );
 obj.position.set(x,y,z);
 return obj;
}

function stem(x,y,z,height,mat,parent=scene) {
 const obj=add(
  new THREE.CylinderGeometry(
   0.035,0.055,height,6
  ),mat,parent
 );
 obj.position.set(x,y,z);
 return obj;
}

function ball(x,y,z,r,mat,parent=scene) {
 const obj=add(
  new THREE.SphereGeometry(r,8,6),
  mat,parent
 );
 obj.position.set(x,y,z);
 return obj;
}

// ========================================
// FARM LANDSCAPE
// ========================================

box(29,0.7,24,M.grass,0,-0.6,0);
box(21,0.3,17,M.soil,0,-0.12,0);

// Central walking paths
box(1.2,0.12,17,M.path,0,0.12,0);
box(21,0.12,1.1,M.path,0,0.12,0);

// Irrigation channels
box(0.85,0.1,17,M.water,-9.7,0.12,0);
box(0.85,0.1,17,M.water,9.7,0.12,0);

// Farm plots
const fields=[];

for(const [x,z] of [
 [-4.8,-4.2],[4.8,-4.2],
 [-4.8,4.2],[4.8,4.2]
]){
 box(7.5,0.4,6.2,M.darkSoil,x,0.2,z);
 box(7.1,0.08,5.8,M.soil,x,0.44,z);

 const plants=new THREE.Group();
 plants.position.set(x,0.49,z);
 scene.add(plants);
 fields.push(plants);
}

// ========================================
// TREES AND FARMHOUSE
// ========================================

function tree(x,z,scale=1) {
 stem(x,0.9*scale,z,1.8*scale,M.trunk);
 ball(x,2.05*scale,z,0.9*scale,M.tree);
 ball(x-0.45*scale,1.8*scale,z,
  0.65*scale,M.leaf);
 ball(x+0.4*scale,1.9*scale,z,
  0.65*scale,M.tree);
}

for(let i=0;i<6;i++){
 tree(-12,-9+i*3.5,0.85);
 tree(12,-9+i*3.5,0.85);
}

box(2.4,1.5,2.1,M.wall,-10.8,0.8,-9);
const roof=box(
 3,0.35,2.7,M.roof,-10.8,1.7,-9
);
roof.rotation.z=-0.14;

// ========================================
// CROP MODELS
// ========================================

function rice(parent,x,z) {
 stem(x,0.37,z,0.72,M.rice,parent);

 for(let i=0;i<4;i++){
  const angle=i*Math.PI/2;
  const leaf=add(
   new THREE.ConeGeometry(0.12,0.55,4),
   i%2?M.riceLight:M.rice,
   parent
  );
  leaf.position.set(
   x+Math.cos(angle)*0.13,
   0.43,
   z+Math.sin(angle)*0.13
  );
  leaf.rotation.z=Math.cos(angle)*0.45;
  leaf.rotation.x=Math.sin(angle)*0.45;
 }

 ball(x,0.77,z,0.075,M.grain,parent);
}

function maize(parent,x,z) {
 stem(x,0.85,z,1.65,M.maize,parent);

 for(let i=0;i<6;i++){
  const angle=i*Math.PI/3;
  const leaf=add(
   new THREE.ConeGeometry(0.17,0.85,4),
   M.maize,parent
  );
  leaf.position.set(
   x+Math.cos(angle)*0.24,
   0.55+i*0.17,
   z+Math.sin(angle)*0.24
  );
  leaf.rotation.z=Math.cos(angle)*0.6;
  leaf.rotation.x=Math.sin(angle)*0.6;
 }

 ball(x+0.13,1.12,z,0.14,M.corn,parent);
}

function legume(parent,x,z) {
 stem(x,0.25,z,0.48,M.legume,parent);

 for(let i=0;i<5;i++){
  const angle=i*Math.PI*2/5;
  const leaf=ball(
   x+Math.cos(angle)*0.23,
   0.32,
   z+Math.sin(angle)*0.23,
   0.18,
   i%2?M.leaf:M.legume,
   parent
  );
  leaf.scale.set(1.25,0.4,0.8);
 }
}

function rootCrop(parent,x,z) {
 for(let i=0;i<5;i++){
  const angle=i*Math.PI*2/5;
  const leaf=ball(
   x+Math.cos(angle)*0.22,
   0.2,
   z+Math.sin(angle)*0.22,
   0.23,M.leaf,parent
  );
  leaf.scale.set(1.1,0.3,0.8);
 }
}

function orchard(parent,x,z) {
 stem(x,0.7,z,1.3,M.trunk,parent);
 ball(x,1.6,z,0.68,M.tree,parent);
 ball(x-0.3,1.4,z,0.45,M.leaf,parent);
}

function classify(id) {
 if(id==="rice")return "rice";
 if(id==="maize")return "maize";

 if(["mung_bean","groundnut","soybean"]
  .includes(id))return "legume";

 if(["banana","durian","coconut"]
  .includes(id))return "orchard";

 return "root";
}

function showCrop(id) {
 const type=classify(id);

 for(const field of fields){
  // Dispose previous crop geometries to avoid
  // increasing GPU memory on repeated changes.
  field.traverse(obj=>{
   if(obj.isMesh){
    obj.geometry.dispose();
   }
  });
  field.clear();

  const spacing={
   rice:0.65,
   maize:1.15,
   legume:0.9,
   root:0.9,
   orchard:2.5
  }[type];

  for(let x=-2.8;x<=2.8;x+=spacing){
   for(let z=-2.2;z<=2.2;z+=spacing){
    if(type==="rice")rice(field,x,z);
    else if(type==="maize")maize(field,x,z);
    else if(type==="legume")legume(field,x,z);
    else if(type==="orchard")orchard(field,x,z);
    else rootCrop(field,x,z);
   }
  }
 }
}

showCrop("rice");

// ========================================
// FARM LABELS AND CONTROLS
// ========================================

const label=document.createElement("div");
label.style.cssText=`
 position:absolute;bottom:14px;left:14px;
 background:#10243ce8;color:white;
 padding:11px 15px;border-radius:12px;
 font:600 13px Segoe UI,Arial;
 pointer-events:none;
`;
label.textContent="Rice field · Drag to rotate · Scroll to zoom";
viewer.appendChild(label);

const reset=document.createElement("button");
reset.textContent="Reset view";
reset.style.cssText=`
 position:absolute;right:12px;bottom:12px;
 z-index:5;padding:9px 13px;
`;
viewer.appendChild(reset);

reset.onclick=()=>{
 camera.position.set(16,15,19);
 controls.target.set(0,0,0);
 controls.update();
};

window.BUMIFarm3D={
 showCrop(id){
  showCrop(id);
  label.textContent=
   id.replaceAll("_"," ").toUpperCase()
   +" · Interactive 3D farm";
 }
};

// ========================================
// CONNECT EXISTING DASHBOARD
// ========================================

// Your current index.html changes the field
// CSS class whenever a crop is selected.
// Watch that change and update the 3D model.

const oldField=document.getElementById("field");

if(oldField){
 const observer=new MutationObserver(()=>{
  const cropName=document.getElementById(
   "fieldCrop"
  )?.textContent?.toLowerCase()||"rice";

  const ids={
   "rice":"rice",
   "maize":"maize",
   "mung bean":"mung_bean",
   "groundnut":"groundnut",
   "soybean":"soybean",
   "sweet potato":"sweet_potato",
   "cassava":"cassava",
   "pineapple":"pineapple",
   "banana":"banana",
   "coconut":"coconut",
   "durian":"durian"
  };

  window.BUMIFarm3D.showCrop(
   ids[cropName]||"rice"
  );
 });

 observer.observe(oldField,{
  attributes:true,
  attributeFilter:["class"]
 });
}

// ========================================
// RESPONSIVE RENDERING
// ========================================

function resize(){
 const w=viewer.clientWidth;
 const h=viewer.clientHeight;
 if(!w||!h)return;
 camera.aspect=w/h;
 camera.updateProjectionMatrix();
 renderer.setSize(w,h);
}

new ResizeObserver(resize).observe(viewer);
resize();

function animate(){
 requestAnimationFrame(animate);
 controls.update();
 renderer.render(scene,camera);
}
animate();
