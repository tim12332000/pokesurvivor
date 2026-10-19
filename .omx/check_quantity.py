"""Exercise quantity cards and actual sandbox combat in headless Chrome."""
from pathlib import Path
from urllib.parse import unquote, urlsplit
import json
import mimetypes
import os
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
URL = 'https://tim12332000.github.io/pokesurvivor/.omx/digimon.html?lang=zh-TW&v=quantity'

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe', headless=True)
    context = browser.new_context(locale='zh-TW', viewport={'width':1280,'height':820}, service_workers='block')
    if os.environ.get('PAGES_LIVE') != '1':
        def proxy(route):
            file = ROOT / unquote(urlsplit(route.request.url).path).removeprefix('/pokesurvivor/')
            if file.is_file():
                route.fulfill(status=200, body=file.read_bytes(), content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream')
            else:
                route.fulfill(status=404, body='Not found')
        context.route('https://tim12332000.github.io/pokesurvivor/**', proxy)
    page = context.new_page()
    errors = []
    missing = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('response', lambda r: missing.append(r.url) if r.status >= 400 else None)
    try:
        page.goto(URL)
        page.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
        if page.locator('#tap-start').is_visible():
            page.locator('#tap-start').click()
        page.evaluate('G.Naruto.choose(30001);G.Flow.play();G.Game.togglePause()')
        report = page.evaluate(r'''() => {
          const assert=(ok,msg)=>{if(!ok)throw Error(msg);},pl=G.Game.player,Q=G.Quantity;
          assert(Q,'Quantity runtime missing');
          const saved={};for(const key of ['isFree','isWall','collide','projectileBlock','propsInCircle','isLiquid'])saved[key]=G.World[key];
          const sees=G.Camera.sees;
          Object.assign(G.World,{isFree:()=>true,isWall:()=>false,collide:()=>{},projectileBlock:()=>false,propsInCircle:()=>[],isLiquid:()=>false});G.Camera.sees=()=>true;
          const enemy=(x=100,y=0)=>{const e=new G.Enemy({dex:19,hp:1e7,spd:0,dmg:0,xp:0,behavior:'chase'},x,y,{hp:1,spd:1,dmg:1});e.types=['normal'];G.EnemyMgr.add(e);G.EnemyMgr.rebuildGrid();return e;};
          const reset=(bonus=2)=>{
            G.Combat.clearFields();G.Projectiles.clear();G.EnemyMgr.clear();G.FX.clear();
            pl.x=pl.y=pl.aim=0;pl.dead=false;pl.hp=pl.maxHp;pl.quantityBonus=bonus;pl.statsTaken={};pl.critChance=0;pl.atkMul=1;
            pl.moves=[];pl.slots=[];pl.active=0;pl.lastPatch=null;pl.buffs.atk={n:0,t:0,amount:0};pl.target=enemy();
          };
          const use=m=>{pl.moves=[m];pl.slots=[[m]];pl.active=0;m.t=0;G.Combat.tick(.001,pl,0);};
          const quantityCard=()=>{for(let i=0;i<30;i++){const c=G.LevelUp.offer(pl,100).find(c=>c.key==='stat:quantity');if(c)return c;}throw Error('Quantity choice never appeared');};
          const ordinary=(kind,count=2)=>Object.assign(G.Moves.instance('ember'),{kind,count,pierce:1,burn:0,poison:0,slow:0,dmg:10,radius:500,range:500,arc:1,width:20,rate:.5,dur:2,life:2,speed:300,size:5,cd:1});
          const out={};
          try {
            reset(0);const stat=G.LevelUp.STATS.find(s=>s.id==='quantity');assert(stat,'Missing quantity stat');
            const card=quantityCard();card.apply(pl);
            assert(Q.bonus(pl)===Q.config.perPick&&pl.statsTaken.quantity===1,'Choice did not record bonus and picked layer');
            const other=new G.Player(pl.mon);assert(Q.bonus(other)===0,'New player inherited quantity');
            for(let i=1;i<Q.config.maxPicks;i++)quantityCard().apply(pl);
            assert(pl.statsTaken.quantity===Q.config.maxPicks&&Q.bonus(pl)===Q.config.maxPicks*Q.config.perPick,'Repeated selections did not reach configured cap');
            assert(Array.from({length:20},()=>G.LevelUp.offer(pl,100)).flat().every(c=>c.key!=='stat:quantity'),'Quantity choice exceeds configured pick limit');
            reset();
            for(const kind of ['projectile','nova','boomerang','cone','orbit']) {
              const m=ordinary(kind),before=JSON.stringify(m);use(m);
              const wanted=Math.max(kind==='nova'?3:kind==='cone'?2:1,2)+2,shots=G.Projectiles.all();
              assert(shots.length===wanted,kind+' quantity '+shots.length+' != '+wanted);
              assert(shots.every(p=>p.owner===pl),'Projectile ownership changed');
              if(['projectile','nova','cone'].includes(kind))assert(shots.every(p=>p.pierce===3),kind+' did not add piercing');
              assert(m.count===2&&m.pierce===1,'Cast mutated learned quantity');out[kind]=shots.length;
              G.Projectiles.clear();
            }
            const piercingVictims=bonus=>{
              reset(bonus);const row=[pl.target,...[160,220,280].map(x=>enemy(x))];
              use(Object.assign(ordinary('projectile',1),{pierce:0,spread:0}));
              const shots=G.Projectiles.all(),first=shots[0];for(const shot of shots.slice(1))G.Projectiles.remove(shot);
              first.x=first.y=first.px=first.py=0;first.vx=300;first.vy=0;
              for(let i=0;i<110;i++){G.Projectiles.update(.01,pl,G.EnemyMgr.all());G.Combat.resolve(.01,pl,i*.01);}
              return row.map(e=>e.hp<1e7);
            };
            assert(JSON.stringify(piercingVictims(0))==='[true,false,false,false]','Baseline projectile piercing fixture');
            assert(JSON.stringify(piercingVictims(2))==='[true,true,true,false]','Bonus piercing did not damage two additional enemies');out.piercing='one versus three actual enemies';
            reset();const victims=[pl.target,...[140,180,220,260,300].map(x=>enemy(x))];use(ordinary('chain'));
            assert(victims.filter(e=>e.hp<1e7).length===4,'Chain target count');out.chain=4;
            for(const kind of ['mine','meteor']) {
              reset();const m=ordinary(kind);use(m);let explosions=0;const ring=G.FX.ring;G.FX.ring=(...args)=>{explosions++;return ring(...args);};
              try{G.Combat.updateFields(kind==='mine'?2.1:1.1);}finally{G.FX.ring=ring;}
              assert(explosions===4,kind+' count '+explosions);assert(pl.target.hp<1e7,kind+' did not damage');out[kind]=explosions;
            }
            reset();const turret=ordinary('turret');for(let i=0;i<8;i++)use(turret);G.Combat.updateFields(.31);
            assert(G.Projectiles.all().length===4,'Turret concurrent cap');out.turret=4;
            reset();const buff=Object.assign(ordinary('buff'),{stat:'atk',amount:.1,stacks:2});for(let i=0;i<8;i++)use(buff);
            assert(pl.buffs.atk.n===4&&buff.stacks===2,'Buff stack cap or learned mutation');out.buffStacks=4;
            reset();const trail=Object.assign(ordinary('trail'),{radius:10});
            for(let i=0;i<24;i++){pl.x=i*30;use(trail);}
            G.Combat.updateFields(.001);
            let ellipses=0;const ctx={save(){},restore(){},beginPath(){},ellipse(){ellipses++;},fill(){},stroke(){}};
            G.Combat.drawGroundFields(ctx);assert(ellipses===40,'Trail concurrent cap '+ellipses/2);out.trail=20;
            reset();const shadow=G.Moves.instance('naruto-shadow-clones');pl.moves=[shadow];pl.slots=[[shadow]];
            assert(G.NarutoClones.limitOf(shadow,pl)===10,'Clone limit missing global quantity');G.NarutoClones.cast(pl,shadow);
            assert(G.NarutoClones.actors.length===10,'Clone actors missing global quantity');
            const add=quantityCard();add.apply(pl);
            assert(G.NarutoClones.actors.length===10+Q.config.perPick,'Passive did not immediately fill clone quota');out.clones=G.NarutoClones.actors.length;
            reset();const shuriken=G.Moves.instance('naruto-shuriken'),base=shuriken.count;
            const mirrored=G.DigimonSkills.fireFrom(pl,shuriken,0,0,0);
            assert(mirrored.length===base+2&&mirrored.length>8,'Clone mimic retained shot cap');assert(shuriken.count===base,'Clone mimic mutated move');out.mirrored=mirrored.length;
            reset(12);const rasen=G.Moves.instance('naruto-rasenshuriken'),explosives=[];
            for(let i=0;i<7;i++)explosives.push(...G.DigimonSkills.fireFrom(pl,rasen,0,0,0));
            assert(explosives.length>80,'Explosive stress fixture did not exceed old cap');
            const victim=pl.target,hp=victim.hp;
            for(const shot of explosives){shot.x=victim.x;shot.y=victim.y;shot.hits.add(victim.id);}
            G.Combat.resolve(0,pl,0);
            const expected=explosives.length*Math.round(rasen.dmg*pl.atk*.8*G.Types.mult(rasen.type,victim.types)*G.Weather.mult(rasen.type));
            assert(Math.abs(hp-victim.hp-expected)<.001,'More than 80 explosives lost splash damage: '+(hp-victim.hp)+' expected '+expected);
            assert(explosives.every(p=>!G.Projectiles.all().includes(p)&&!p.digiBomb),'Explosive cleanup retained spent shots');out.explosiveSplash=explosives.length;
            reset();const learned=G.Moves.instance('ember');G.Moves.levelUp(learned);const raw=learned.count;
            const snap=Q.snapshot(pl,learned);assert(snap.count===raw+2&&learned.count===raw,'Upgrade double-applied quantity');
            assert(Q.snapshot(pl,snap).count===snap.count,'Repeated snapshot double-applied quantity');
            while(learned.lvl<learned.def.maxLvl)G.Moves.levelUp(learned);
            assert(G.Moves.evolve(learned),'Evolution fixture failed');
            const again=Q.snapshot(pl,learned);assert(again.count===learned.count+2,'Evolution double-applied quantity');
            pl.quantityBonus=0;const upgradeFirst=G.Moves.instance('ember');
            while(upgradeFirst.lvl<upgradeFirst.def.maxLvl)G.Moves.levelUp(upgradeFirst);
            G.Moves.evolve(upgradeFirst);pl.quantityBonus=2;
            assert(Q.snapshot(pl,upgradeFirst).count===again.count,'Passive and upgrade/evolution order changed quantity');
            const custom=Object.assign(ordinary('projectile',2),{digimonSkill:true,digiMode:'shot',digiVis:{proj:'ball',pal:'fire'},charge:.2});
            use(custom);pl.quantityBonus=9;G.Combat.updateFields(.21);
            assert(G.Projectiles.all().length===4,'Queued cast did not retain quantity snapshot');assert(custom.count===2,'Charged cast mutated move');out.charged=4;
            const comboLoss=bonus=>{
              reset(bonus);const e=pl.target;e.x=40;G.EnemyMgr.rebuildGrid();let hits=0,total=0;const hurt=e.hurt;e.hurt=function(d,...args){hits++;total+=d;return hurt.call(this,d,...args);};
              const move=Object.assign(ordinary('melee',2),{digimonSkill:true,digiMode:'melee',digiVis:{melee:'claw',pal:'fire'},burstInterval:.02});
              G.DigimonSkills.cast(pl,move);for(let i=0;i<10;i++)G.Combat.updateFields(.02);return {hits,total};
            };
            const plain=comboLoss(0),boost=comboLoss(2);assert(plain.hits===2&&boost.hits===4,'Custom melee hit quantity');
            assert(Math.abs(boost.total/boost.hits-plain.total/plain.hits)<1e-6,'Bonus melee hits lost per-hit damage');out.combo={plain,boost};
            reset();pl.mon=G.Naruto.records.get(30008);pl.dex=30008;
            const flames=G.Moves.instance('naruto-black-flames');for(let i=0;i<7;i++)G.DigimonSkills.cast(pl,flames);
            assert(G.NarutoOffense.effects.filter(f=>f.kind==='black-flames').length===4,'Amaterasu concurrent cap');out.amaterasu=4;
            G.Combat.clearFields();G.Projectiles.clear();assert(!G.NarutoOffense.effects.length&&!G.DigimonSkills.activeEffects.length&&!G.NarutoClones.actors.length,'Scene cleanup leaked effects');
            return out;
          }finally{Object.assign(G.World,saved);G.Camera.sees=sees;G.Combat.clearFields();G.Projectiles.clear();}
        }''')
        page.evaluate('''() => {
          G.Game.quit();G.Flow.goMenu();G.Naruto.choose(30001);G.Flow.play();
          if(G.Quantity.bonus(G.Game.player)!==0)throw Error('Fresh run did not reset quantity');
          window.quantityOriginalOffer=G.LevelUp.offer;
          G.LevelUp.offer=(pl,n=3)=>{for(let i=0;i<30;i++){const cards=window.quantityOriginalOffer(pl,100),card=cards.find(c=>c.key==='stat:quantity');if(card)return [card,...cards.filter(c=>c!==card)].slice(0,n);}throw Error('Quantity choice never appeared for UI');};
          G.Game.debugLevelUp();
        }''')
        page.locator('#scr-levelup').wait_for(state='visible')
        assert '數量增幅' in page.locator('#cards .card').first.inner_text()
        page.screenshot(path=str(ROOT / '.omx/quantity-card.png'), animations='disabled')
        page.locator('#cards .card').first.click()
        page.wait_for_function('G.Quantity.bonus(G.Game.player)===G.Quantity.config.perPick&&G.Game.player.statsTaken.quantity===1')
        page.evaluate('G.LevelUp.offer=window.quantityOriginalOffer;G.Game.quit();G.Flow.goMenu()')
        assert not errors, errors
        assert not missing, missing
        print(json.dumps({'passed':report,'actualChoiceUI':'passed','freshRunReset':'passed','pageErrors':errors,'missing':missing}, ensure_ascii=False))
    finally:
        browser.close()
