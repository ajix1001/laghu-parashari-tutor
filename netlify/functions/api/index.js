"use strict";
/**
 * Laghu Parashari — Complete Jyotisha API as a single Netlify Function
 * Routes: /api/*  (redirected from netlify.toml)
 * Uses astronomy-engine for planetary positions (VSOP87, IAU standards)
 */
const Astronomy = require("astronomy-engine");

// ─── Constants ───────────────────────────────────────────────────────────────
const SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
               "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"];
const SIGN_IDX = Object.fromEntries(SIGNS.map((s,i)=>[s,i]));

const PLANETS_CLASSICAL = ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn"];
const VIMSHOTTARI_SEQ   = ["Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury"];
const VIMSHOTTARI_YEARS = {Ketu:7,Venus:20,Sun:6,Moon:10,Mars:7,Rahu:18,Jupiter:16,Saturn:19,Mercury:17};
const TOTAL_DASHA_YEARS = 120;

// 27 Nakshatras (index → {name, lord, startDeg})
const NAKSHATRAS = [
  {name:"Ashwini",lord:"Ketu",start:0},{name:"Bharani",lord:"Venus",start:13.333},
  {name:"Krittika",lord:"Sun",start:26.667},{name:"Rohini",lord:"Moon",start:40},
  {name:"Mrigashira",lord:"Mars",start:53.333},{name:"Ardra",lord:"Rahu",start:66.667},
  {name:"Punarvasu",lord:"Jupiter",start:80},{name:"Pushya",lord:"Saturn",start:93.333},
  {name:"Ashlesha",lord:"Mercury",start:106.667},{name:"Magha",lord:"Ketu",start:120},
  {name:"Purva Phalguni",lord:"Venus",start:133.333},{name:"Uttara Phalguni",lord:"Sun",start:146.667},
  {name:"Hasta",lord:"Moon",start:160},{name:"Chitra",lord:"Mars",start:173.333},
  {name:"Swati",lord:"Rahu",start:186.667},{name:"Vishakha",lord:"Jupiter",start:200},
  {name:"Anuradha",lord:"Saturn",start:213.333},{name:"Jyeshtha",lord:"Mercury",start:226.667},
  {name:"Mula",lord:"Ketu",start:240},{name:"Purva Ashadha",lord:"Venus",start:253.333},
  {name:"Uttara Ashadha",lord:"Sun",start:266.667},{name:"Shravana",lord:"Moon",start:280},
  {name:"Dhanishtha",lord:"Mars",start:293.333},{name:"Shatabhisha",lord:"Rahu",start:306.667},
  {name:"Purva Bhadrapada",lord:"Jupiter",start:320},{name:"Uttara Bhadrapada",lord:"Saturn",start:333.333},
  {name:"Revati",lord:"Mercury",start:346.667}
];
const NAKSATRA_SPAN = 360 / 27; // 13.3333°

// ─── Ayanamsa (Lahiri / Chitrapaksha) ────────────────────────────────────────
function lahiriAyanamsa(jd) {
  const T0 = 1827424.5, rate = 50.2388475, yr = 365.242189623;
  return ((rate * (jd - T0) / yr) / 3600) % 360;
}

// ─── Ephemeris helpers ────────────────────────────────────────────────────────
function astroBody(name) {
  const map = {
    Sun:Astronomy.Body.Sun, Moon:Astronomy.Body.Moon,
    Mars:Astronomy.Body.Mars, Mercury:Astronomy.Body.Mercury,
    Jupiter:Astronomy.Body.Jupiter, Venus:Astronomy.Body.Venus,
    Saturn:Astronomy.Body.Saturn,
  };
  return map[name];
}

function tropicalLon(name, time) {
  const body = astroBody(name);
  const ec = Astronomy.Ecliptic(Astronomy.GeoVector(body, time, false));
  return ((ec.elon % 360) + 360) % 360;
}

function bodySpeed(name, time) {
  const jd = time.tt;
  const t1 = Astronomy.MakeTime(new Date((jd - 0.5 - 2451545.0) * 86400000 + Date.UTC(2000,0,1,12)));
  const t2 = Astronomy.MakeTime(new Date((jd + 0.5 - 2451545.0) * 86400000 + Date.UTC(2000,0,1,12)));
  const body = astroBody(name);
  const e1 = Astronomy.Ecliptic(Astronomy.GeoVector(body, t1, false));
  const e2 = Astronomy.Ecliptic(Astronomy.GeoVector(body, t2, false));
  let diff = e2.elon - e1.elon;
  if (diff > 180) diff -= 360;
  if (diff < -180) diff += 360;
  return diff;
}

function rahuTropical(jd) {
  const T = (jd - 2451545.0) / 36525.0;
  const omega = 125.04452 - 1934.136261*T + 0.0020708*T*T + T*T*T/450000.0;
  return ((omega % 360) + 360) % 360;
}

function computeLagna(time, lat, lon) {
  // SiderealTime returns Greenwich Apparent Sidereal Time (GAST) in hours.
  // Add observer longitude (in hours) to get Local Sidereal Time (LST).
  const gast = Astronomy.SiderealTime(time);       // hours, Greenwich
  const lst   = ((gast + lon / 15) % 24 + 24) % 24; // local sidereal time
  const lstRad = lst * Math.PI / 12;               // convert hours→radians
  const T = (time.tt - 2451545.0) / 36525.0;
  const eps = (23.439291111 - 0.013004167*T) * Math.PI / 180;
  const latRad = lat * Math.PI / 180;
  // Ascendant = atan2(-cos(lst), sin(lst)*cos(eps)+tan(lat)*sin(eps)) + 180
  const asc = Math.atan2(-Math.cos(lstRad),
    Math.sin(lstRad)*Math.cos(eps) + Math.tan(latRad)*Math.sin(eps));
  return (((asc * 180 / Math.PI) + 180) % 360 + 360) % 360;
}

function wholeSignHouse(lagnaIdx, signIdx) {
  return ((signIdx - lagnaIdx + 12) % 12) + 1;
}

// ─── Chart calculation ────────────────────────────────────────────────────────
function calculateChart({birth_date, birth_hour, birth_minute, latitude, longitude, tz_offset}) {
  const [y,m,d] = birth_date.split("-").map(Number);
  const utHours = birth_hour + birth_minute/60 - tz_offset;
  const utDate = new Date(Date.UTC(y, m-1, d) + utHours * 3600000);
  const time = Astronomy.MakeTime(utDate);
  const jd = time.tt + 2451545.0;  // Julian Day (TT)

  const ayanamsa = lahiriAyanamsa(jd);
  const tropAsc  = computeLagna(time, latitude, longitude);
  const siderAsc = ((tropAsc - ayanamsa) % 360 + 360) % 360;
  const lagnaIdx = Math.floor(siderAsc / 30);
  const lagnaSign = SIGNS[lagnaIdx];

  // Planets
  const planets = {};
  for (const name of PLANETS_CLASSICAL) {
    const tropLon  = tropicalLon(name, time);
    const siderLon = ((tropLon - ayanamsa) % 360 + 360) % 360;
    const signIdx  = Math.floor(siderLon / 30);
    const speed    = bodySpeed(name, time);
    planets[name] = {
      longitude:    +siderLon.toFixed(4),
      sign:         SIGNS[signIdx],
      sign_deg:     +(siderLon - signIdx*30).toFixed(4),
      house:        wholeSignHouse(lagnaIdx, signIdx),
      is_retrograde: speed < 0 && name !== "Sun" && name !== "Moon",
    };
  }

  // Rahu / Ketu
  const rahuTrop    = rahuTropical(jd);
  const rahuSider   = ((rahuTrop - ayanamsa) % 360 + 360) % 360;
  const ketuSider   = (rahuSider + 180) % 360;
  for (const [name, lon] of [["Rahu", rahuSider], ["Ketu", ketuSider]]) {
    const signIdx = Math.floor(lon / 30);
    planets[name] = {
      longitude:    +lon.toFixed(4),
      sign:         SIGNS[signIdx],
      sign_deg:     +(lon - signIdx*30).toFixed(4),
      house:        wholeSignHouse(lagnaIdx, signIdx),
      is_retrograde: true,
    };
  }

  // House occupants
  const houseOccupants = {};
  for (let i = 1; i <= 12; i++) houseOccupants[i] = [];
  for (const [name, info] of Object.entries(planets)) {
    houseOccupants[info.house].push(name);
  }

  return {
    julian_day:      +jd.toFixed(6),
    ayanamsa:        +ayanamsa.toFixed(4),
    lagna_degrees:   +siderAsc.toFixed(4),
    lagna_sign:      lagnaSign,
    planets,
    house_occupants: houseOccupants,
  };
}

// ─── Nakshatra & Dasha ────────────────────────────────────────────────────────
function getNakshatra(moonLon) {
  const idx  = Math.floor(moonLon / NAKSATRA_SPAN);
  const nak  = NAKSHATRAS[idx];
  const frac = (moonLon - nak.start) / NAKSATRA_SPAN;
  return { nakshatra: nak.name, lord: nak.lord, fraction_elapsed: +frac.toFixed(6) };
}

function daysToYMD(totalDays) {
  const years  = Math.floor(totalDays / 365.25);
  const rem1   = totalDays - years * 365.25;
  const months = Math.floor(rem1 / 30.4375);
  const days   = Math.round(rem1 - months * 30.4375);
  return { years, months, days };
}

function birthBalance(birth_date, moon_degrees) {
  const nak = getNakshatra(moon_degrees);
  const lord = nak.lord;
  const dashYears = VIMSHOTTARI_YEARS[lord];
  const balanceYears = dashYears * (1 - nak.fraction_elapsed);
  const balanceDays  = balanceYears * 365.25;
  return {
    nakshatra_name:    nak.nakshatra,
    nakshatra_lord:    lord,
    fraction_elapsed:  +nak.fraction_elapsed.toFixed(6),
    balance_years:     +balanceYears.toFixed(4),
    balance_days:      +balanceDays.toFixed(2),
    balance_ymd:       daysToYMD(balanceDays),
  };
}

function addYears(date, years) {
  const ms = years * 365.25 * 86400000;
  return new Date(date.getTime() + ms);
}

function mahadashaTimeline(birth_date, moon_degrees) {
  const nak = getNakshatra(moon_degrees);
  const startLord = nak.lord;
  const seqStart  = VIMSHOTTARI_SEQ.indexOf(startLord);
  const balYears  = VIMSHOTTARI_YEARS[startLord] * (1 - nak.fraction_elapsed);

  const birthDate = new Date(birth_date + "T00:00:00Z");
  const timeline  = [];
  let cursor      = new Date(birthDate.getTime() - (VIMSHOTTARI_YEARS[startLord] - balYears) * 365.25 * 86400000);

  for (let i = 0; i < 9; i++) {
    const lord = VIMSHOTTARI_SEQ[(seqStart + i) % 9];
    const years = VIMSHOTTARI_YEARS[lord];
    const end   = addYears(cursor, years);
    const isPartial = i === 0;
    timeline.push({
      lord,
      years,
      start_date: cursor.toISOString().slice(0, 10),
      end_date:   end.toISOString().slice(0, 10),
      is_partial: isPartial,
    });
    cursor = end;
  }
  return { timeline };
}

function currentDasha(birth_date, moon_degrees, query_date) {
  const qDate = query_date ? new Date(query_date + "T00:00:00Z") : new Date();
  const tl = mahadashaTimeline(birth_date, moon_degrees).timeline;

  let maha = null;
  for (const m of tl) {
    const s = new Date(m.start_date + "T00:00:00Z");
    const e = new Date(m.end_date   + "T00:00:00Z");
    if (qDate >= s && qDate < e) { maha = m; break; }
  }
  if (!maha) return { mahadasha: null, antardasha: null };

  // Compute antardasha within maha
  const mahaStart = new Date(maha.start_date + "T00:00:00Z");
  const mIdx      = VIMSHOTTARI_SEQ.indexOf(maha.lord);
  let cursor      = new Date(mahaStart);
  let antar       = null;
  let antarIdx    = -1;
  for (let i = 0; i < 9; i++) {
    const sub   = VIMSHOTTARI_SEQ[(mIdx + i) % 9];
    const yrs   = (VIMSHOTTARI_YEARS[maha.lord] * VIMSHOTTARI_YEARS[sub]) / TOTAL_DASHA_YEARS;
    const end   = addYears(cursor, yrs);
    if (qDate >= cursor && qDate < end) {
      antar = { sub_lord: sub, start_date: cursor.toISOString().slice(0, 10), end_date: end.toISOString().slice(0, 10) };
      antarIdx = i;
      break;
    }
    cursor = end;
  }

  // Compute pratyantardasha within antar
  let pratya = null;
  if (antar) {
    const aIdx     = (mIdx + antarIdx) % 9;
    let cursor2    = new Date(antar.start_date + "T00:00:00Z");
    const antarYrs = (VIMSHOTTARI_YEARS[maha.lord] * VIMSHOTTARI_YEARS[antar.sub_lord]) / TOTAL_DASHA_YEARS;
    for (let i = 0; i < 9; i++) {
      const sub2 = VIMSHOTTARI_SEQ[(aIdx + i) % 9];
      const yrs2 = (antarYrs * VIMSHOTTARI_YEARS[sub2]) / TOTAL_DASHA_YEARS;
      const end2 = addYears(cursor2, yrs2);
      if (qDate >= cursor2 && qDate < end2) {
        pratya = { sub2_lord: sub2, start_date: cursor2.toISOString().slice(0, 10), end_date: end2.toISOString().slice(0, 10) };
        break;
      }
      cursor2 = end2;
    }
  }

  return { mahadasha: maha, antardasha: antar, pratyantardasha: pratya };
}

function antardashaList(major_lord, mahadasha_start, partial_balance_days) {
  const mIdx  = VIMSHOTTARI_SEQ.indexOf(major_lord);
  let cursor  = new Date(mahadasha_start + "T00:00:00Z");
  const list  = [];
  for (let i = 0; i < 9; i++) {
    const sub      = VIMSHOTTARI_SEQ[(mIdx + i) % 9];
    const yrs      = (VIMSHOTTARI_YEARS[major_lord] * VIMSHOTTARI_YEARS[sub]) / TOTAL_DASHA_YEARS;
    const totalDays = yrs * 365.25;
    const end      = addYears(cursor, yrs);
    list.push({
      sub_lord:     sub,
      start_date:   cursor.toISOString().slice(0, 10),
      end_date:     end.toISOString().slice(0, 10),
      years:        +yrs.toFixed(4),
      duration_ymd: daysToYMD(totalDays),
    });
    cursor = end;
  }
  return { antardashas: list };
}

// ─── Lordship rules (Laghu Parashari) ────────────────────────────────────────
const KENDRA   = new Set([1,4,7,10]);
const TRIKONA  = new Set([1,5,9]);
const TRISHADAYA = new Set([3,6,11]);
const MARAKA   = new Set([2,7]);
const NAT_BENEFICS = new Set(["Jupiter","Venus","Mercury","Moon"]);
const NAT_MALEFICS = new Set(["Sun","Mars","Saturn","Rahu","Ketu"]);

function housesOfPlanet(planet, lagna) {
  const lagnaIdx = SIGN_IDX[lagna];
  // Each sign ruler — simplified mapping
  const RULERS = {
    Aries:"Mars",Taurus:"Venus",Gemini:"Mercury",Cancer:"Moon",
    Leo:"Sun",Virgo:"Mercury",Libra:"Venus",Scorpio:"Mars",
    Sagittarius:"Jupiter",Capricorn:"Saturn",Aquarius:"Saturn",Pisces:"Jupiter"
  };
  const houses = [];
  for (let i = 0; i < 12; i++) {
    const signName = SIGNS[(lagnaIdx + i) % 12];
    if (RULERS[signName] === planet) houses.push(i + 1);
  }
  return houses;
}

function evaluatePlanet(planet, lagna) {
  const houses = housesOfPlanet(planet, lagna);
  if (!houses.length) return { planet, functional_nature: "Neutral", nature: "Neutral", score: 0, owned_houses: houses, houses, notes: [] };

  let score = 0;
  const notes = [];

  for (const h of houses) {
    if (TRIKONA.has(h) && h !== 1) { score += 3; notes.push(`Lord of trikona ${h}`); }
    if (h === 1) { score += 2; notes.push("Lagna lord (always auspicious)"); }
    if (TRISHADAYA.has(h)) { score -= 2; notes.push(`Lord of trishadaya ${h}`); }
    if (h === 8 && !houses.includes(1)) { score -= 2; notes.push("Lord of 8th (dusthana)"); }
    if (MARAKA.has(h)) { score -= 1; notes.push(`Maraka lord of ${h}`); }
    if (KENDRA.has(h) && NAT_BENEFICS.has(planet)) { score -= 1; notes.push(`Kendradhipati dosha (benefic in kendra ${h})`); }
    if (KENDRA.has(h) && NAT_MALEFICS.has(planet)) { score += 1; notes.push(`Kendradhipati relief (malefic in kendra ${h})`); }
  }

  const ownedKendras  = houses.filter(h => KENDRA.has(h) && h !== 1);
  const ownedTrikonas = houses.filter(h => TRIKONA.has(h) && h !== 1);
  const isYogaKaraka  = ownedKendras.length > 0 && ownedTrikonas.length > 0;
  if (isYogaKaraka) { score += 3; notes.push("Yoga Karaka!"); }
  if (houses.includes(1) && score < 2) score = 2;

  let nature;
  if (isYogaKaraka)   nature = "Yoga Karaka";
  else if (score >= 3) nature = "Auspicious";
  else if (score >= 1) nature = "Mixed";
  else if (score === 0) nature = "Neutral";
  else if (score >= -1) nature = "Maraka";
  else                 nature = "Inauspicious";

  return { planet, functional_nature: nature, nature, score, owned_houses: houses, houses, notes, is_yoga_karaka: isYogaKaraka };
}

function lagnaProfile(lagna) {
  const allPlanets = ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn"];
  // Return as array (frontend uses .forEach) with functional_nature + owned_houses fields
  const planet_evaluations = allPlanets.map(p => evaluatePlanet(p, lagna));
  return { lagna, planet_evaluations };
}

// ─── Yoga analysis ────────────────────────────────────────────────────────────
function yogaAnalysis(lagna, planet_positions) {
  const posMap   = Object.fromEntries((planet_positions||[]).map(p => [p.planet, p.house]));
  const raja_yogas = [];
  const marakas    = [];

  const allP = ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn"];
  for (const p of allP) {
    const ev = evaluatePlanet(p, lagna);
    if (ev.is_yoga_karaka) {
      raja_yogas.push({
        yoga_type:      "Yoga Karaka",
        sambandha_type: "Single-planet",
        planets:        [p],
        description:    `${p} owns both a kendra and a trikona for ${lagna} lagna, making it the most powerful planet.`,
      });
    }
    if (ev.nature === "Maraka") {
      marakas.push({
        planet:      p,
        severity:    "Primary",
        description: `${p} rules the ${ev.owned_houses.join(" & ")} house(s), maraka positions for ${lagna} lagna.`,
      });
    }
  }

  // Raja yoga by conjunction
  const houseToPlants = {};
  for (const [p, h] of Object.entries(posMap)) {
    if (!houseToPlants[h]) houseToPlants[h] = [];
    houseToPlants[h].push(p);
  }
  for (const [h, planets] of Object.entries(houseToPlants)) {
    if (planets.length < 2) continue;
    const kendraLords  = planets.filter(p => housesOfPlanet(p, lagna).some(hh => KENDRA.has(hh) && hh !== 1));
    const trikonaLords = planets.filter(p => housesOfPlanet(p, lagna).some(hh => TRIKONA.has(hh) && hh !== 1));
    const kl = kendraLords.filter(p => !trikonaLords.includes(p));
    if (kl.length > 0 && trikonaLords.length > 0) {
      raja_yogas.push({
        yoga_type:      "Raja Yoga",
        sambandha_type: "Conjunction",
        planets:        [...new Set([...kl, ...trikonaLords])],
        description:    `Kendra lord(s) ${kl.join("+")} and trikona lord(s) ${trikonaLords.join("+")} conjunct in house ${h}.`,
      });
    }
  }

  return { lagna, raja_yogas, marakas };
}

// ─── Ascendant profiles ───────────────────────────────────────────────────────
const ASCENDANT_PROFILES = {
  Aries:        { lagna_lord:"Mars", auspicious:["Sun","Mars","Jupiter"],      inauspicious:["Mercury","Venus","Saturn"],  yoga_karaka:[], marakas:["Venus","Mercury"], notes:"Mars rules 1st & 8th; avoid 8th lordship. Saturn as 10th & 11th lord is highly malefic." },
  Taurus:       { lagna_lord:"Venus", auspicious:["Venus","Mercury","Saturn"], inauspicious:["Jupiter","Moon"],            yoga_karaka:["Saturn"], marakas:["Mars","Jupiter"], notes:"Saturn rules 9th & 10th — Yoga Karaka. Jupiter as 8th & 11th lord is inauspicious." },
  Gemini:       { lagna_lord:"Mercury", auspicious:["Mercury","Venus","Saturn"],inauspicious:["Mars","Jupiter"],           yoga_karaka:[], marakas:["Mars","Saturn"], notes:"Mercury is lagna lord. Saturn as 8th & 9th lord is mixed. Mars as 6th & 11th is malefic." },
  Cancer:       { lagna_lord:"Moon", auspicious:["Moon","Mars","Jupiter"],     inauspicious:["Mercury","Venus","Saturn"],  yoga_karaka:["Mars"], marakas:["Mercury","Saturn"], notes:"Mars rules 5th & 10th — Yoga Karaka. Saturn as 7th & 8th lord is a double maraka/dusthana." },
  Leo:          { lagna_lord:"Sun", auspicious:["Sun","Mars","Jupiter"],       inauspicious:["Mercury","Venus","Saturn"],  yoga_karaka:[], marakas:["Mercury","Saturn"], notes:"Sun rules only lagna. Mars as 4th & 9th lord is very auspicious. Saturn as 6th & 7th is malefic." },
  Virgo:        { lagna_lord:"Mercury", auspicious:["Mercury","Venus"],        inauspicious:["Mars","Jupiter","Moon"],     yoga_karaka:[], marakas:["Mars","Jupiter"], notes:"Venus rules 2nd & 9th — very auspicious. Jupiter as 4th & 7th has kendradhipati dosha." },
  Libra:        { lagna_lord:"Venus", auspicious:["Venus","Mercury","Saturn"], inauspicious:["Jupiter","Sun","Mars"],      yoga_karaka:["Saturn"], marakas:["Mars","Jupiter"], notes:"Saturn rules 4th & 5th — Yoga Karaka. Sun as 11th lord is inauspicious." },
  Scorpio:      { lagna_lord:"Mars", auspicious:["Moon","Jupiter","Sun"],      inauspicious:["Mercury","Venus"],           yoga_karaka:[], marakas:["Mercury","Venus"], notes:"Jupiter rules 2nd & 5th — highly auspicious. Moon as 9th lord is favorable." },
  Sagittarius:  { lagna_lord:"Jupiter", auspicious:["Jupiter","Mars","Sun"],   inauspicious:["Venus","Mercury","Saturn"],  yoga_karaka:[], marakas:["Saturn","Venus"], notes:"Mars rules 5th & 12th — 5th lordship dominates. Venus as 6th & 11th is inauspicious." },
  Capricorn:    { lagna_lord:"Saturn", auspicious:["Saturn","Mercury","Venus"],inauspicious:["Moon","Mars","Jupiter"],     yoga_karaka:["Venus"], marakas:["Moon","Mars"], notes:"Venus rules 5th & 10th — Yoga Karaka. Jupiter as 3rd & 12th is inauspicious." },
  Aquarius:     { lagna_lord:"Saturn", auspicious:["Saturn","Venus","Mercury"],inauspicious:["Moon","Jupiter","Mars"],     yoga_karaka:["Venus"], marakas:["Moon","Mars"], notes:"Venus rules 4th & 9th — Yoga Karaka. Mars as 3rd & 10th has mixed effects." },
  Pisces:       { lagna_lord:"Jupiter", auspicious:["Jupiter","Moon","Mars"],  inauspicious:["Mercury","Venus","Saturn"],  yoga_karaka:[], marakas:["Mars","Saturn"], notes:"Moon as 5th lord is very auspicious. Saturn as 11th & 12th is highly inauspicious." },
};

// ─── Interpretation ───────────────────────────────────────────────────────────
const HOUSE_SIGNIFICATIONS = {
  1:"self, vitality, personality",2:"wealth, speech, family",3:"courage, siblings, communication",
  4:"home, mother, happiness",5:"intellect, children, past karma",6:"enemies, disease, service",
  7:"spouse, partnerships, public life",8:"longevity, transformation, hidden matters",
  9:"dharma, guru, fortune",10:"career, fame, authority",11:"gains, desires, elder siblings",
  12:"liberation, loss, foreign lands"
};
const PLANET_SIGNIFICATIONS = {
  Sun:"soul, authority, father, vitality",Moon:"mind, mother, emotions, public",
  Mars:"energy, courage, siblings, property",Mercury:"intellect, communication, trade",
  Jupiter:"wisdom, dharma, children, expansion",Venus:"beauty, pleasure, spouse, luxury",
  Saturn:"discipline, karma, servants, longevity",Rahu:"obsession, illusion, foreign",Ketu:"liberation, detachment, past life"
};
const QUALITY_MAP = {
  "Yoga Karaka": { label:"exceptionally favorable", color:"#1a6600" },
  Auspicious:    { label:"favorable",               color:"#2a6000" },
  Mixed:         { label:"mixed results",           color:"#7a6000" },
  Neutral:       { label:"neutral influence",       color:"#555555" },
  Maraka:        { label:"death-inflicting caution",color:"#8b4500" },
  Inauspicious:  { label:"challenging",             color:"#8b0000" },
};

function interpretDasha(lagna, maha_lord, antar_lord) {
  const mahaEval  = evaluatePlanet(maha_lord, lagna);
  const antarEval = antar_lord ? evaluatePlanet(antar_lord, lagna) : null;
  const mahaQ     = QUALITY_MAP[mahaEval.nature] || QUALITY_MAP.Neutral;
  const antarQ    = antarEval ? (QUALITY_MAP[antarEval.nature] || QUALITY_MAP.Neutral) : null;

  const mahaH = mahaEval.owned_houses.join(" & ");
  const mahaS = PLANET_SIGNIFICATIONS[maha_lord] || maha_lord;

  let combined = `The <strong>${maha_lord} Mahadasha</strong> is <em>${mahaQ.label}</em> for ${lagna} lagna. `;
  combined += `${maha_lord} rules the ${mahaH} house(s), activating themes of <em>${HOUSE_SIGNIFICATIONS[mahaEval.owned_houses[0]] || "life"}</em> `;
  combined += `and signifies ${mahaS}. `;
  if (mahaEval.is_yoga_karaka) combined += `As <strong>Yoga Karaka</strong>, this is one of the most powerful dasha periods. `;
  if (antarEval && antar_lord) {
    const antarH = antarEval.owned_houses.join(" & ");
    combined += `During the <strong>${antar_lord} Antardasha</strong> (${antarQ.label}), emphasis shifts to the ${antarH} house, `;
    combined += `activating <em>${HOUSE_SIGNIFICATIONS[antarEval.owned_houses[0]] || "life"}</em>.`;
  }

  // Areas activated
  const areas_activated = [
    ...mahaEval.owned_houses.map(h => HOUSE_SIGNIFICATIONS[h]),
    ...(antarEval ? antarEval.owned_houses.map(h => HOUSE_SIGNIFICATIONS[h]) : []),
  ].filter(Boolean);

  // Cautions for dusthana houses
  const cautions = [];
  const dusthana = new Set([6, 8, 12]);
  for (const h of mahaEval.owned_houses) {
    if (dusthana.has(h)) cautions.push(`${maha_lord} rules the ${h}th house (dusthana) — challenges in ${HOUSE_SIGNIFICATIONS[h]} possible.`);
  }

  return {
    quality:           mahaEval.nature,
    quality_color:     mahaQ.color.replace("#", ""),
    combined,
    areas_activated,
    cautions,
    summary:           combined,
    mahadasha_nature:  mahaEval.nature,
    mahadasha_color:   mahaQ.color,
    antardasha_nature: antarEval?.nature || null,
    antardasha_color:  antarQ?.color || null,
  };
}

function interpretLagna(lagna) {
  const profile = ASCENDANT_PROFILES[lagna];
  if (!profile) return { narrative: `No profile for ${lagna}.`, summary: `No profile for ${lagna}.` };
  return {
    lagna,
    lagna_lord:   profile.lagna_lord,
    narrative:    profile.notes,
    summary:      profile.notes,
    auspicious:   profile.auspicious,
    inauspicious: profile.inauspicious,
    yoga_karaka:  profile.yoga_karaka,
    marakas:      profile.marakas,
    notes:        profile.notes,
  };
}

// ─── Kundali SVG ─────────────────────────────────────────────────────────────
const SIGN_ABBR = {Aries:"Ar",Taurus:"Ta",Gemini:"Ge",Cancer:"Ca",Leo:"Le",Virgo:"Vi",
                   Libra:"Li",Scorpio:"Sc",Sagittarius:"Sg",Capricorn:"Cp",Aquarius:"Aq",Pisces:"Pi"};
const PLANET_ABBR  = {Sun:"Su",Moon:"Mo",Mars:"Ma",Mercury:"Me",Jupiter:"Ju",Venus:"Ve",Saturn:"Sa",Rahu:"Ra",Ketu:"Ke"};
const PLANET_COLOR = {Sun:"#b35900",Moon:"#2e3b55",Mars:"#8b0000",Mercury:"#2a6000",
                      Jupiter:"#5c3d00",Venus:"#6b0060",Saturn:"#333333",Rahu:"#555500",Ketu:"#004455"};

function generateKundaliSvg({ lagna_sign, house_occupants, retrograde = [], size = 360 }) {
  const S = size, M = S/2, Q = S/4;
  const TL=[0,0],TR=[S,0],BR=[S,S],BL=[0,S];
  const MT=[M,0],MR=[S,M],MB=[M,S],ML=[0,M];
  const A=[Q,Q],B=[S-Q,Q],C=[M,M],D=[Q,S-Q],E=[S-Q,S-Q];

  const cen = (...pts) => [pts.reduce((s,p)=>s+p[0],0)/pts.length, pts.reduce((s,p)=>s+p[1],0)/pts.length];
  const mid = (p1,p2) => [(p1[0]+p2[0])/2,(p1[1]+p2[1])/2];

  const HOUSES = {
    1: {pts:[MT,B,C,A],   tc:cen(MT,B,C,A)},
    2: {pts:[TL,MT,A],    tc:mid(MT,A)},
    3: {pts:[TL,A,ML],    tc:mid(A,ML)},
    4: {pts:[ML,A,C,D],   tc:cen(ML,A,C,D)},
    5: {pts:[BL,ML,D],    tc:mid(ML,D)},
    6: {pts:[BL,D,MB],    tc:mid(D,MB)},
    7: {pts:[MB,D,C,E],   tc:cen(MB,D,C,E)},
    8: {pts:[BR,E,MB],    tc:mid(E,MB)},
    9: {pts:[BR,MR,E],    tc:mid(MR,E)},
    10:{pts:[MR,E,C,B],   tc:cen(MR,E,C,B)},
    11:{pts:[TR,B,MR],    tc:mid(B,MR)},
    12:{pts:[TR,MT,B],    tc:mid(MT,B)},
  };

  const lagnaIdx = SIGNS.indexOf(lagna_sign);
  const retSet   = new Set(retrograde);
  const svg = [];

  svg.push(`<svg xmlns="http://www.w3.org/2000/svg" width="${S}" height="${S}" viewBox="0 0 ${S} ${S}" style="font-family:'Crimson Pro',serif">`);
  svg.push(`<rect width="${S}" height="${S}" fill="#f4ead5" rx="2"/>`);

  for (const [h, hd] of Object.entries(HOUSES)) {
    const pts = hd.pts.map(p=>p.join(",")).join(" ");
    const fill = +h===1 ? "rgba(255,244,220,1)" : "#f4ead5";
    svg.push(`<polygon points="${pts}" fill="${fill}" stroke="none"/>`);
  }

  const lw="1.3", lc="#4b3621";
  const line=(p1,p2)=>`<line x1="${p1[0].toFixed(2)}" y1="${p1[1].toFixed(2)}" x2="${p2[0].toFixed(2)}" y2="${p2[1].toFixed(2)}" stroke="${lc}" stroke-width="${lw}"/>`;
  svg.push(line(MT,MR),line(MR,MB),line(MB,ML),line(ML,MT));
  svg.push(line(TL,BR),line(TR,BL));
  svg.push(`<rect x="1" y="1" width="${S-2}" height="${S-2}" fill="none" stroke="${lc}" stroke-width="1.8"/>`);

  for (const [h, hd] of Object.entries(HOUSES)) {
    const hnum = +h;
    const [cx, cy] = hd.tc;
    const signIdx = (lagnaIdx + hnum - 1) % 12;
    const abbr = SIGN_ABBR[SIGNS[signIdx]] || "?";

    if (hnum === 1) svg.push(`<circle cx="${MT[0].toFixed(2)}" cy="${MT[1].toFixed(2)}" r="4.5" fill="#8b0000" opacity="0.85"/>`);

    svg.push(`<text x="${cx.toFixed(2)}" y="${(cy-4).toFixed(2)}" text-anchor="middle" font-size="8.5" fill="#9b7b5b" font-family="'IM Fell English SC',serif">${hnum}</text>`);
    const sc = hnum===1 ? "#8b0000" : "#4b3621";
    svg.push(`<text x="${cx.toFixed(2)}" y="${(cy+7).toFixed(2)}" text-anchor="middle" font-size="7.5" fill="${sc}" opacity="0.7">${abbr}</text>`);

    const planets = (house_occupants[hnum] || house_occupants[String(hnum)] || []);
    let py = cy + 18;
    for (const planet of planets) {
      const pa = PLANET_ABBR[planet] || planet.slice(0,2);
      const col = PLANET_COLOR[planet] || "#333";
      const retro = retSet.has(planet) ? "℞" : "";
      svg.push(`<text x="${cx.toFixed(2)}" y="${py.toFixed(2)}" text-anchor="middle" font-size="9" font-weight="600" fill="${col}">${pa}${retro}</text>`);
      py += 10.5;
    }
  }
  svg.push("</svg>");
  return svg.join("\n");
}

// ─── Prashna (Horary) ────────────────────────────────────────────────────────
const PRASHNA_CATEGORIES = {
  career:       { label:"Career & Work",            houses:[10,6,11], keywords:["career","job","work","promotion","salary","boss","office","profession","business","employment","interview"] },
  marriage:     { label:"Marriage",                 houses:[7,2,11],  keywords:["marry","marriage","wedding","engagement","spouse","husband","wife","alliance","matrimony"] },
  relationship: { label:"Love & Relationship",      houses:[7,5],     keywords:["love","romance","boyfriend","girlfriend","crush","relationship","partner","dating","breakup"] },
  children:     { label:"Children",                 houses:[5,9,11],  keywords:["child","children","baby","pregnancy","conceive","son","daughter","kid"] },
  finance:      { label:"Money & Finance",          houses:[2,11,5],  keywords:["money","wealth","finance","income","loan","debt","investment","savings","rich","fund","buy","afford"] },
  education:    { label:"Education & Exams",        houses:[4,5,9],   keywords:["study","exam","education","degree","admission","college","university","school","course","result"] },
  health:       { label:"Health",                   houses:[1,6,8],   keywords:["health","disease","illness","sick","surgery","recover","cure","medical","doctor","hospital","pain"] },
  travel:       { label:"Travel & Relocation",      houses:[3,9,12],  keywords:["travel","journey","trip","abroad","foreign","visa","relocate","move","migration","immigration"] },
  property:     { label:"Home & Property",          houses:[4,11],    keywords:["house","property","land","home","apartment","real estate","rent","buy a house"] },
  litigation:   { label:"Legal & Disputes",         houses:[6,8,7],   keywords:["court","lawsuit","legal","litigation","dispute","case","police","fight","enemy","lawyer"] },
  lost_object:  { label:"Lost Object / Missing",    houses:[2,4,7],   keywords:["lost","missing","stolen","find","recover","where is"] },
  spiritual:    { label:"Spiritual Path",           houses:[9,12,5],  keywords:["spiritual","moksha","liberation","guru","god","sadhana","meditation","dharma"] },
  general:      { label:"General Guidance",         houses:[1,10,7],  keywords:[] },
};

const MOVABLE_SIGNS = new Set(["Aries","Cancer","Libra","Capricorn"]);
const FIXED_SIGNS   = new Set(["Taurus","Leo","Scorpio","Aquarius"]);

function detectCategory(question) {
  const q = (question || "").toLowerCase();
  let best = "general", hits = 0;
  for (const [cat, meta] of Object.entries(PRASHNA_CATEGORIES)) {
    let n = 0;
    for (const kw of meta.keywords) {
      const re = new RegExp(`\\b${kw.replace(/[-/\\^$*+?.()|[\]{}]/g, "\\$&")}`, "i");
      if (re.test(q)) n++;
    }
    if (n > hits) { hits = n; best = cat; }
  }
  return best;
}

function signNature(sign) {
  if (MOVABLE_SIGNS.has(sign))
    return { label:"Movable (Chara)", hint:"Quick results, change is favoured — outcome unfolds soon." };
  if (FIXED_SIGNS.has(sign))
    return { label:"Fixed (Sthira)",  hint:"Delay or status-quo — the situation resists change; outcome is slow." };
  return   { label:"Dual (Dwiswabhava)", hint:"Partial or repeat results — the matter resolves in stages, not at once." };
}

function ord(n){return ({1:"1st",2:"2nd",3:"3rd"})[n] || `${n}th`;}

function angularDistance(h1, h2){ return ((h2 - h1 + 12) % 12) || 12; }

function hasClassicalAspect(fromHouse, toHouse, planet) {
  const d = angularDistance(fromHouse, toHouse);
  if (d === 7) return true;
  if (planet === "Mars"    && (d === 4 || d === 8))  return true;
  if (planet === "Jupiter" && (d === 5 || d === 9))  return true;
  if (planet === "Saturn"  && (d === 3 || d === 10)) return true;
  if ((planet === "Rahu" || planet === "Ketu") && (d === 5 || d === 9)) return true;
  return false;
}

function scoreToVerdict(score) {
  if (score >=  6) return { verdict:"Yes — Strongly Favoured",     color:"gold",   headline:"The chart speaks clearly in your favour." };
  if (score >=  3) return { verdict:"Yes — Favoured",              color:"indigo", headline:"The signs lean toward a positive outcome." };
  if (score >=  1) return { verdict:"Mixed — Cautiously Hopeful",  color:"indigo", headline:"Some support, but expect partial results or effort." };
  if (score >= -2) return { verdict:"Uncertain — Wait & Watch",    color:"ochre",  headline:"The picture is unclear. Avoid major commitments now." };
  if (score >= -5) return { verdict:"Unfavourable — Likely No",    color:"ochre",  headline:"The signs are against the matter at this time." };
  return             { verdict:"No — Strongly Against",            color:"red",    headline:"The chart strongly counsels against this path." };
}

const ELEMENT_DIRECTION = {
  Aries:"East", Leo:"East", Sagittarius:"East",
  Taurus:"South", Virgo:"South", Capricorn:"South",
  Gemini:"West", Libra:"West", Aquarius:"West",
  Cancer:"North", Scorpio:"North", Pisces:"North",
};

function evaluatePrashna(chart, category) {
  const meta      = PRASHNA_CATEGORIES[category];
  const primaryH  = meta.houses[0];
  const otherHs   = meta.houses.slice(1);
  const lagna     = chart.lagna_sign;
  const lagnaIdx  = SIGN_IDX[lagna];
  const planets   = chart.planets;
  const occ       = chart.house_occupants;

  const SIGN_LORD = {Aries:"Mars",Taurus:"Venus",Gemini:"Mercury",Cancer:"Moon",
                     Leo:"Sun",Virgo:"Mercury",Libra:"Venus",Scorpio:"Mars",
                     Sagittarius:"Jupiter",Capricorn:"Saturn",Aquarius:"Saturn",Pisces:"Jupiter"};

  const lagnaLord     = SIGN_LORD[lagna];
  const lagnaLordEval = evaluatePlanet(lagnaLord, lagna);
  const lagnaLordH    = planets[lagnaLord]?.house;

  const matterSign    = SIGNS[(lagnaIdx + primaryH - 1) % 12];
  const matterLord    = SIGN_LORD[matterSign];
  const matterLordH   = planets[matterLord]?.house;
  const matterEval    = evaluatePlanet(matterLord, lagna);

  const moonH         = planets["Moon"]?.house;
  const moonEval      = evaluatePlanet("Moon", lagna);

  // Connections between lagna lord and matter lord
  const connections = [];
  if (lagnaLord === matterLord) {
    connections.push(`${lagnaLord} rules both the lagna and the matter — the querent IS the matter; very direct involvement.`);
  } else {
    if (lagnaLordH === matterLordH) {
      connections.push(`${lagnaLord} (lagna lord) and ${matterLord} (lord of ${ord(primaryH)}) are conjunct in the ${ord(lagnaLordH)} house — strong yoga of querent and matter.`);
    }
    if (hasClassicalAspect(lagnaLordH, matterLordH, lagnaLord) ||
        hasClassicalAspect(matterLordH, lagnaLordH, matterLord)) {
      connections.push(`${lagnaLord} and ${matterLord} are in mutual aspect — the querent and the matter are linked.`);
    }
    const llSign = SIGNS[(lagnaIdx + (lagnaLordH ?? 1) - 1) % 12];
    const mlSign = SIGNS[(lagnaIdx + (matterLordH ?? 1) - 1) % 12];
    if (SIGN_LORD[llSign] === matterLord && SIGN_LORD[mlSign] === lagnaLord) {
      connections.push(`${lagnaLord} and ${matterLord} are in parivartana (mutual exchange) — the highest form of yoga; outcome strongly tied to wish.`);
    }
  }

  // Influences on the primary house
  const occupants = occ[primaryH] || occ[String(primaryH)] || [];
  const supports = [], afflictions = [];

  for (const p of occupants) {
    const ev = evaluatePlanet(p, lagna);
    if (ev.is_yoga_karaka) {
      supports.push(`${p} (Yoga Karaka) sits in the ${ord(primaryH)} house — a powerful blessing on the matter.`);
    } else if (ev.nature === "Auspicious") {
      supports.push(`${p} (functional benefic) occupies the ${ord(primaryH)} house.`);
    } else if (ev.nature === "Inauspicious" || ev.nature === "Maraka") {
      afflictions.push(`${p} (functional malefic) afflicts the ${ord(primaryH)} house.`);
    } else if (NAT_BENEFICS.has(p)) {
      supports.push(`${p} (natural benefic) sits in the ${ord(primaryH)} house.`);
    } else if (NAT_MALEFICS.has(p)) {
      afflictions.push(`${p} (natural malefic) sits in the ${ord(primaryH)} house.`);
    }
  }

  for (const [p, info] of Object.entries(planets)) {
    if (occupants.includes(p)) continue;
    if (hasClassicalAspect(info.house, primaryH, p)) {
      const ev = evaluatePlanet(p, lagna);
      if (ev.is_yoga_karaka) {
        supports.push(`${p} (Yoga Karaka) aspects the ${ord(primaryH)} house — a strong supporting influence.`);
      } else if (ev.nature === "Auspicious") {
        supports.push(`${p} (functional benefic) aspects the ${ord(primaryH)} house.`);
      } else if (ev.nature === "Inauspicious" || ev.nature === "Maraka") {
        afflictions.push(`${p} (functional malefic) aspects the ${ord(primaryH)} house.`);
      }
    }
  }

  // Score
  let score = 0;
  const factors = [];
  const f = (text, delta) => { factors.push({factor:text, weight:delta}); score += delta; };

  if (lagnaLordEval.is_yoga_karaka)
    f(`${lagnaLord} (lagna lord) is the Yoga Karaka — querent's position is strong.`, 3);
  else if ([1,4,5,7,9,10,11].includes(lagnaLordH))
    f(`${lagnaLord} (lagna lord) sits in a supportive ${ord(lagnaLordH)} house.`, 2);
  else if ([6,8,12].includes(lagnaLordH))
    f(`${lagnaLord} (lagna lord) is afflicted in the ${ord(lagnaLordH)} house — querent is under stress.`, -2);

  if (matterEval.is_yoga_karaka)
    f(`${matterLord} (lord of the ${ord(primaryH)}) is the Yoga Karaka — exceptional support for the matter.`, 3);
  else if ([1,4,5,7,9,10,11].includes(matterLordH))
    f(`${matterLord} (lord of the ${ord(primaryH)}) is well-placed in the ${ord(matterLordH)} house.`, 2);
  else if ([6,8,12].includes(matterLordH)) {
    const rel = ((matterLordH - primaryH) % 12 + 12) % 12;
    if ([5,7,11].includes(rel))
      f(`${matterLord} (lord of the ${ord(primaryH)}) falls in the ${ord(matterLordH)} — loss/affliction of the matter.`, -3);
    else
      f(`${matterLord} (lord of the ${ord(primaryH)}) is in a dusthana (${ord(matterLordH)}).`, -2);
  }

  if (connections.length)
    f("Lagna lord is connected to the lord of the matter (yoga of querent + matter).", 3);

  if (supports.length)
    f(`Functional benefic influences on the ${ord(primaryH)} house: ${supports.length}.`, supports.length);
  if (afflictions.length) {
    factors.push({factor:`Functional malefic influences on the ${ord(primaryH)} house: ${afflictions.length}.`, weight:-afflictions.length});
    score -= afflictions.length;
  }

  if ([6,8,12].includes(moonH))
    f(`Moon is in the ${ord(moonH)} house — the mind is anxious or unsettled at the moment of asking.`, -1);
  else if (moonEval.nature === "Auspicious" || moonEval.is_yoga_karaka)
    f("Moon is functionally auspicious — the mind is clear and the question is sincere.", 1);

  const jupH = planets["Jupiter"]?.house;
  if (jupH === 1 || hasClassicalAspect(jupH, 1, "Jupiter"))
    f("Jupiter aspects or sits in the lagna — divine grace upholds the question.", 2);
  if (jupH === moonH || hasClassicalAspect(jupH, moonH, "Jupiter"))
    f("Jupiter influences the Moon — the mind is supported by wisdom.", 1);

  const v = scoreToVerdict(score);
  const sn = signNature(lagna);

  let addendum = null;
  if (category === "lost_object") {
    const itemSign = SIGNS[(lagnaIdx + 3) % 12];
    addendum = `Lost-object hint: the 4th house from lagna (${itemSign}) suggests the object is in the ${ELEMENT_DIRECTION[itemSign] || "?"} direction or near a place with that element's qualities.`;
  }

  return {
    category, category_label: meta.label,
    primary_house: primaryH, other_houses: otherHs,
    lagna_sign: lagna, lagna_nature: sn.label,
    lagna_lord: lagnaLord, lagna_lord_house: lagnaLordH,
    matter_lord: matterLord, matter_lord_house: matterLordH,
    moon_house: moonH,
    connections, supports, afflictions, factors,
    score,
    verdict: v.verdict, color: v.color, headline: v.headline,
    timing_hint: sn.hint,
    addendum,
  };
}

function castPrashna(body) {
  const askedAt = body.asked_at ? new Date(body.asked_at) : new Date();
  // Convert UTC moment to local civil time using tz_offset (hours east of UTC)
  const localMs = askedAt.getTime() + (body.tz_offset * 3600 * 1000);
  const local = new Date(localMs);
  // Use UTC accessors on `local` to extract the local civil clock components
  const chart = calculateChart({
    birth_date: `${local.getUTCFullYear()}-${String(local.getUTCMonth()+1).padStart(2,"0")}-${String(local.getUTCDate()).padStart(2,"0")}`,
    birth_hour: local.getUTCHours(),
    birth_minute: local.getUTCMinutes(),
    latitude: body.latitude,
    longitude: body.longitude,
    tz_offset: body.tz_offset,
  });

  const cat = (body.category && PRASHNA_CATEGORIES[body.category])
    ? body.category : detectCategory(body.question);
  const interpretation = evaluatePrashna(chart, cat);

  const retro = Object.entries(chart.planets)
    .filter(([,info])=>info.is_retrograde).map(([n])=>n);
  const kundali_svg = generateKundaliSvg({
    lagna_sign: chart.lagna_sign,
    house_occupants: chart.house_occupants,
    retrograde: retro,
  });

  return {
    question: body.question,
    asked_at_utc: askedAt.toISOString(),
    location: { latitude: body.latitude, longitude: body.longitude, tz_offset: body.tz_offset },
    chart,
    interpretation,
    kundali_svg,
  };
}

// ─── Router ───────────────────────────────────────────────────────────────────
function jsonResp(body, status=200) {
  return {
    statusCode: status,
    headers: {
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
    },
    body: JSON.stringify(body),
  };
}
function svgResp(body) {
  return {
    statusCode: 200,
    headers: { "Content-Type": "image/svg+xml", "Access-Control-Allow-Origin": "*" },
    body,
  };
}
function err(msg, status=400) {
  return jsonResp({ detail: msg }, status);
}

exports.handler = async (event) => {
  if (event.httpMethod === "OPTIONS") return { statusCode: 204, headers:{"Access-Control-Allow-Origin":"*","Access-Control-Allow-Methods":"GET,POST,OPTIONS","Access-Control-Allow-Headers":"Content-Type"}, body:"" };

  // Strip the function path prefix so we see /charts/ephemeris etc.
  let path = event.path || "";
  // Netlify sets path as full path: /.netlify/functions/api/charts/ephemeris
  path = path.replace(/^\/?\.?netlify\/functions\/api/, "").replace(/^\/api/, "") || "/";

  const method = event.httpMethod;
  let body = {};
  try { if (event.body) body = JSON.parse(event.body); } catch {}

  try {
    // Charts
    if (path === "/charts/ephemeris" && method === "POST") {
      return jsonResp(calculateChart(body));
    }
    if (path === "/charts/kundali-svg" && method === "POST") {
      return svgResp(generateKundaliSvg(body));
    }
    if (path === "/charts/interpret-dasha" && method === "POST") {
      return jsonResp(interpretDasha(body.lagna, body.maha_lord, body.antar_lord));
    }
    if (path.startsWith("/charts/interpret-lagna") && method === "POST") {
      const lagna = new URL("http://x"+event.rawUrl).searchParams.get("lagna") || body.lagna;
      return jsonResp(interpretLagna(lagna));
    }

    // Dasha
    if (path === "/dasha/birth-balance" && method === "POST") {
      return jsonResp(birthBalance(body.birth_date, body.moon_degrees));
    }
    if (path === "/dasha/mahadasha-timeline" && method === "POST") {
      return jsonResp(mahadashaTimeline(body.birth_date, body.moon_degrees));
    }
    if (path === "/dasha/current" && method === "POST") {
      return jsonResp(currentDasha(body.birth_date, body.moon_degrees, body.query_date));
    }
    if (path === "/dasha/antardasha" && method === "POST") {
      return jsonResp(antardashaList(body.major_lord, body.mahadasha_start, body.partial_balance_days));
    }

    // Lordship
    if (path === "/lordship/lagna-profile" && method === "POST") {
      return jsonResp(lagnaProfile(body.lagna));
    }
    if (path === "/lordship/evaluate-planet" && method === "POST") {
      return jsonResp(evaluatePlanet(body.planet, body.lagna));
    }

    // Yoga
    if ((path === "/yoga/analyse" || path === "/yoga/analyze") && method === "POST") {
      return jsonResp(yogaAnalysis(body.lagna, body.planet_positions));
    }

    // Ascendants
    const ascMatch = path.match(/^\/ascendants\/(.+)$/);
    if (ascMatch && method === "GET") {
      const lagna = decodeURIComponent(ascMatch[1]);
      const p = ASCENDANT_PROFILES[lagna];
      if (!p) return err(`No profile for ${lagna}`, 404);
      return jsonResp({ lagna, ...p });
    }

    // Prashna
    if (path === "/prashna/categories" && method === "GET") {
      return jsonResp({
        categories: Object.entries(PRASHNA_CATEGORIES).map(([key, m]) => ({
          key, label: m.label, houses: m.houses, keywords: m.keywords,
        })),
      });
    }
    if (path === "/prashna/ask" && method === "POST") {
      if (!body.question || typeof body.question !== "string" || body.question.length < 2)
        return err("question is required (min 2 chars).", 400);
      if (typeof body.latitude !== "number" || typeof body.longitude !== "number" || typeof body.tz_offset !== "number")
        return err("latitude, longitude and tz_offset are required numbers.", 400);
      if (body.category && !PRASHNA_CATEGORIES[body.category])
        return err(`Unknown category '${body.category}'.`, 400);
      return jsonResp(castPrashna(body));
    }

    // Health
    if (path === "/" || path === "") return jsonResp({ status:"online", version:"2.0.0" });
    if (path === "/health")         return jsonResp({ status:"healthy" });

    return err(`Route not found: ${path}`, 404);
  } catch (e) {
    console.error(e);
    return err("Internal error: " + e.message, 500);
  }
};
