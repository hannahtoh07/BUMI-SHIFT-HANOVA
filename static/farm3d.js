
/*
 BUMI SHIFT — Farm Futures 3D
 HANOVA | Sarawak

 Procedural interactive 3D agricultural scene.
 Uses Three.js from a CDN.

 The visualization is illustrative.
 It does not predict actual plant growth.
*/

import * as THREE from
 "https://esm.sh/three@0.160.1";

import { OrbitControls } from
 "https://esm.sh/three@0.160.1/examples/jsm/controls/OrbitControls.js";

const container = document.getElementById("farm3d");

if (!container) {
 throw new Error("Missing #farm3d container");
}

const scene = new THREE.Scene();
scene.background = new THREE.Color("#b9e3f5");
scene.fog = new THREE.Fog("#b9e3f5", 32, 75);

const camera = new THREE.PerspectiveCamera(
 42, 1, 0.1, 150
);
camera.position.set(16, 13, 19);

const renderer = new THREE.WebGLRenderer({
 antialias: true
});
renderer.setPixelRatio(
 Math.min(window.devicePixelRatio, 2)
);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type =
 THREE.PCFSoftShadowMap;
renderer.outputColorSpace =
 THREE.SRGBColorSpace;
renderer.toneMapping =
 THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.45;

container.appendChild(renderer.domElement);

const controls = new OrbitControls(
 camera, renderer.domElement
);
controls.enableDamping = true;
controls.dampingFactor = 0.07;
controls.target.set(0, 0.5, 0);
controls.minDistance = 7;
controls.maxDistance = 38;
controls.maxPolarAngle = Math.PI * 0.48;

scene.add(new THREE.HemisphereLight(
 0xffffff, 0x668b70, 2.2
));

const sunlight = new THREE.DirectionalLight(
 0xfff0ce, 3
);
sunlight.position.set(-9, 17, 11);
sunlight.castShadow = true;
sunlight.shadow.mapSize.set(2048, 2048);
sunlight.shadow.camera.left = -20;
sunlight.shadow.camera.right = 20;
sunlight.shadow.camera.top = 20;
sunlight.shadow.camera.bottom = -20;
scene.add(sunlight);

function mat(color, roughness = 0.85) {
 return new THREE.MeshStandardMaterial({
  color, roughness
 });
}

const materials = {
 grass: mat("#619b56"),
 soil: mat("#76523b"),
 soilDark: mat("#60412d"),
 water: new THREE.MeshStandardMaterial({
  color: "#48b7d7",
  metalness: 0.15,
  roughness: 0.24,
  transparent: true,
  opacity: 0.88
 }),
 path: mat("#d7b77e"),
 wood: mat("#986b43"),
 trunk: mat("#78513b"),
 leaves: mat("#317f46"),
 rice: mat("#4b9f4c"),
 riceLight: mat("#8cc95b"),
 grain: mat("#dfc16a"),
 maize: mat("#46934b"),
 maizeDark: mat("#287e3f"),
 corn: mat("#efc653"),
 legume: mat("#2d9a5b"),
 legumeLight: mat("#63c982"),
 flower: mat("#f4d17e"),
 root: mat("#529f50"),
 roof: mat("#b56e4d"),
 wall: mat("#eed7ae")
};

function mesh(geometry, material, parent = scene) {
 const object = new THREE.Mesh(
  geometry, material
 );
 object.castShadow = true;
 object.receiveShadow = true;
 parent.add(object);
 return object;
}

function box(w, h, d, material, x, y, z,
 parent = scene) {
 const object = mesh(
  new THREE.BoxGeometry(w, h, d),
  material, parent
 );
 object.position.set(x, y, z);
 return object;
}

function cylinder(top, bottom, height,
 material, x, y, z, parent = scene) {
 const object = mesh(
  new THREE.CylinderGeometry(
   top, bottom, height, 7
  ),
  material, parent
 );
 object.position.set(x, y, z);
 return object;
}

function sphere(radius, material, x, y, z,
 parent = scene) {
 const object = mesh(
  new THREE.SphereGeometry(
   radius, 8, 6
  ),
  material, parent
 );
 object.position.set(x, y, z);
 return object;
}

// ==========================================
// LANDSCAPE
// ==========================================

box(
 30, 0.65, 25,
 materials.grass, 0, -0.5, 0
);

box(
 20, 0.4, 17,
 materials.soil, 0, -0.15, 0
);

// Main walking paths
box(
 1.25, 0.12, 17,
 materials.path, 0, 0.12, 0
);

box(
 20, 0.12, 1.05,
 materials.path, 0, 0.12, 0
);

// Irrigation canals
box(
 0.8, 0.12, 16,
 materials.water, -9.2, 0.13, 0
);

box(
 0.8, 0.12, 16,
 materials.water, 9.2, 0.13, 0
);

// Raised field plots
const fieldPositions = [
 [-4.7, -4.1],
 [4.7, -4.1],
 [-4.7, 4.1],
 [4.7, 4.1]
];

const cropGroups = [];

for (const [x, z] of fieldPositions) {
 box(
  7.5, 0.35, 6.3,
  materials.soilDark,
  x, 0.15, z
 );

 box(
  7.1, 0.08, 5.9,
  materials.soil,
  x, 0.37, z
 );

 const group = new THREE.Group();
 group.position.set(x, 0.42, z);
 scene.add(group);
 cropGroups.push(group);
}

// ==========================================
// SURROUNDING TREES
// ==========================================

function addTree(x, z, scale = 1) {
 cylinder(
  0.13 * scale,
  0.19 * scale,
  1.7 * scale,
  materials.trunk,
  x, 0.9 * scale, z
 );

 for (const [dx, dy, dz, r] of [
  [0, 2.05, 0, 0.85],
  [-0.42, 1.75, 0, 0.65],
  [0.38, 1.85, 0.2, 0.7]
 ]) {
  sphere(
   r * scale,
   materials.leaves,
   x + dx * scale,
   dy * scale,
   z + dz * scale
  );
 }
}

for (let i = 0; i < 7; i++) {
 addTree(-12.3, -10 + i * 3.2, 0.8);
 addTree(12.3, -10 + i * 3.2, 0.8);
}

// Farm hut
box(
 2.5, 1.5, 2.2,
 materials.wall,
 -10.5, 0.8, -9
);

const roof = box(
 3.0, 0.3, 2.8,
 materials.roof,
 -10.5, 1.72, -9
);
roof.rotation.z = -0.13;

// Fence posts
for (let x = -10; x <= 10; x += 2) {
 for (const z of [-8.7, 8.7]) {
  cylinder(
   0.06, 0.07, 0.9,
   materials.wood, x, 0.45, z
  );
 }
}

// ==========================================
// CROP MODELS
// ==========================================

function ricePlant(parent, x, z) {
 cylinder(
  0.025, 0.035, 0.75,
  materials.rice, x, 0.4, z, parent
 );

 for (let i = 0; i < 5; i++) {
  const angle = i * Math.PI * 2 / 5;

  const leaf = mesh(
   new THREE.ConeGeometry(
    0.11, 0.6, 4
   ),
   i % 2
    ? materials.riceLight
    : materials.rice,
   parent
  );

  leaf.position.set(
   x + Math.cos(angle) * 0.13,
   0.47,
   z + Math.sin(angle) * 0.13
  );

  leaf.rotation.z =
   Math.cos(angle) * 0.42;

  leaf.rotation.x =
   Math.sin(angle) * 0.42;
 }

 for (let i = 0; i < 3; i++) {
  sphere(
   0.055, materials.grain,
   x + i * 0.065 - 0.065,
   0.78 + i * 0.035,
   z,
   parent
  );
 }
}

function maizePlant(parent, x, z) {
 cylinder(
  0.055, 0.075, 1.7,
  materials.maizeDark,
  x, 0.88, z, parent
 );

 for (let i = 0; i < 6; i++) {
  const angle = i * Math.PI / 3;

  const leaf = mesh(
   new THREE.ConeGeometry(
    0.18, 0.95, 4
   ),
   materials.maize,
   parent
  );

  leaf.position.set(
   x + Math.cos(angle) * 0.25,
   0.65 + i * 0.16,
   z + Math.sin(angle) * 0.25
  );

  leaf.rotation.z =
   Math.cos(angle) * 0.6;
  leaf.rotation.x =
   Math.sin(angle) * 0.6;
 }

 sphere(
  0.15, materials.corn,
  x + 0.15, 1.15, z, parent
 );
}

function legumePlant(parent, x, z) {
 cylinder(
  0.025, 0.04, 0.45,
  materials.legume,
  x, 0.25, z, parent
 );

 for (let i = 0; i < 5; i++) {
  const angle = i * Math.PI * 2 / 5;

  const leaf = sphere(
   0.18,
   i % 2
    ? materials.legume
    : materials.legumeLight,
   x + Math.cos(angle) * 0.23,
   0.32 + (i % 2) * 0.12,
   z + Math.sin(angle) * 0.23,
   parent
  );

  leaf.scale.set(1.2, 0.35, 0.75);
 }

 sphere(
  0.065, materials.flower,
  x, 0.52, z, parent
 );
}

function rootPlant(parent, x, z) {
 for (let i = 0; i < 5; i++) {
  const angle = i * Math.PI * 2 / 5;

  const leaf = sphere(
   0.22, materials.root,
   x + Math.cos(angle) * 0.22,
   0.20,
   z + Math.sin(angle) * 0.22,
   parent
  );

  leaf.scale.set(1.1, 0.3, 0.9);
 }
}

function orchardPlant(parent, x, z) {
 cylinder(
  0.09, 0.12, 1.2,
  materials.trunk,
  x, 0.62, z, parent
 );

 sphere(
  0.62, materials.leaves,
  x, 1.45, z, parent
 );

 sphere(
  0.43, materials.legumeLight,
  x - 0.25, 1.3, z, parent
 );
}

function classifyCrop(id) {
 if (id === "rice") return "rice";
 if (id === "maize") return "maize";

 if ([
  "mung_bean",
  "groundnut",
  "soybean"
 ].includes(id)) return "legume";

 if ([
  "durian",
  "coconut",
  "banana"
 ].includes(id)) return "orchard";

 return "root";
}

function displayCrop(cropId) {
 const type = classifyCrop(cropId);

 for (const group of cropGroups) {
  group.clear();

  const spacing =
   type === "orchard" ? 2.3 :
   type === "maize" ? 1.1 :
   type === "rice" ? 0.57 : 0.8;

  for (let x = -2.9; x <= 2.9; x += spacing) {
   for (let z = -2.35; z <= 2.35; z += spacing) {
    if (type === "rice") {
     ricePlant(group, x, z);
    } else if (type === "maize") {
     maizePlant(group, x, z);
    } else if (type === "legume") {
     legumePlant(group, x, z);
    } else if (type === "orchard") {
     orchardPlant(group, x, z);
    } else {
     rootPlant(group, x, z);
    }
   }
  }
 }
}

window.BUMIFarm3D = {
 showCrop: displayCrop,
 resetCamera() {
  camera.position.set(16, 13, 19);
  controls.target.set(0, 0.5, 0);
  controls.update();
 }
};

displayCrop("rice");

// ==========================================
// RENDER LOOP
// ==========================================

function resize() {
 const w = container.clientWidth;
 const h = container.clientHeight;

 if (!w || !h) return;

 camera.aspect = w / h;
 camera.updateProjectionMatrix();
 renderer.setSize(w, h);
}

new ResizeObserver(resize).observe(container);
resize();

function animate() {
 requestAnimationFrame(animate);
 controls.update();
 renderer.render(scene, camera);
}

animate();
