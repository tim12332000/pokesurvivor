"""Exercise the eight Naruto kits in the actual browser combat runtime.

Local files are served under the Pages origin unless PAGES_LIVE=1 is explicit.
"""
from pathlib import Path
from urllib.parse import urlsplit, unquote
from playwright.sync_api import sync_playwright
import json
import mimetypes
import os

ROOT = Path(__file__).resolve().parent.parent
URL = 'https://tim12332000.github.io/pokesurvivor/.omx/digimon.html?lang=zh-TW&v=naruto-eight-kits'

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
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.on('response', lambda response: missing.append(response.url) if response.status >= 400 else None)
    try:
        page.goto(URL)
        page.wait_for_function("document.getElementById('boot').classList.contains('hidden')")
        if page.locator('#tap-start').is_visible():
            page.locator('#tap-start').click()
        page.evaluate('G.Naruto.choose(30003);G.Flow.play();G.Game.togglePause()')
        report = page.evaluate(r'''() => {
          const assert=(ok,msg)=>{if(!ok)throw Error(msg);};
          const pl=G.Game.player, catalog=G.NarutoSkillCatalog;
          const saved={};
          for(const key of ['isWall','isFree','collide','propsInCircle','projectileBlock','isLiquid'])saved[key]=G.World[key];
          Object.assign(G.World,{isWall:()=>false,isFree:()=>true,collide:()=>{},propsInCircle:()=>[],projectileBlock:()=>false,isLiquid:()=>false});
          let time=0;
          const step=seconds=>{
            for(let t=0;t<seconds;t+=1/120){
              time+=1/120;G.Projectiles.update(1/120,pl,G.EnemyMgr.all());
              G.Combat.resolve(1/120,pl,time);G.Combat.updateFields(1/120);G.FX.update(1/120);
            }
          };
          const setup=(dex,points=[])=>{
            G.Combat.clearFields();G.Projectiles.clear();G.FX.clear();G.EnemyMgr.clear();
            const mon=G.Naruto.records.get(dex);
            pl.mon=mon;pl.dex=dex;pl.x=pl.y=0;pl.aim=0;pl.hp=pl.maxHp;
            pl.dead=false;pl.invuln=0;pl.level=1;pl.atkMul=pl.spdMul=1;pl.critChance=0;
            pl.moves=[];pl.slots=[];pl.bind={};pl.banned=new Set();pl.active=0;
            pl.addMove(mon.start);
            const enemies=points.map(([x,y])=>{
              const enemy=new G.Enemy({dex:19,hp:100000,spd:0,dmg:5,xp:0,behavior:'chase'},x,y,{hp:1,spd:1,dmg:1});
              enemy.types=['normal'];G.EnemyMgr.add(enemy);return enemy;
            });
            G.EnemyMgr.rebuildGrid();pl.target=enemies[0]||null;return enemies;
          };
          const cast=(id,level=1)=>G.DigimonSkills.cast(pl,G.Moves.instance(id,level));
          const loss=enemy=>100000-enemy.hp;
          const close=(a,b,epsilon=.001)=>Math.abs(a-b)<epsilon;
          const result={};
          try {
            assert(catalog.definitions.size===26,'Expected 26 distinct ninja skills including shared tools');
            const rosters=[];
            for(const mon of G.Naruto.records.values()) {
              setup(mon.dex);pl.level=6;
              const pool=G.Moves.poolFor(mon);
              assert(new Set(pool).size===5,'Character does not have exactly three identity skills and two tools: '+mon.dex);
              assert(pool.includes('naruto-kunai')&&pool.includes('naruto-shuriken'),'Missing shared tools: '+mon.dex);
              const privateIds=pool.filter(id=>!['naruto-kunai','naruto-shuriken'].includes(id));
              assert(privateIds.includes(mon.start),'Starting move missing from pool: '+mon.dex);
              const later=privateIds.filter(id=>id!==mon.start);
              pl.level=2;let cards=G.LevelUp.offer(pl);
              assert(!cards.some(card=>later.some(id=>card.key==='new:'+id)),'Character skill offered before training level: '+mon.dex);
              pl.level=3;cards=G.LevelUp.offer(pl);
              let card=cards.find(card=>later.some(id=>card.key==='new:'+id));
              assert(card,'Missing guaranteed level 3 skill: '+mon.dex);assert(card.apply(pl)!==false,'Level 3 skill apply failed');
              const learned=pl.moves.find(move=>later.includes(move.id)).id;
              pl.addMove('naruto-kunai');pl.addMove('naruto-shuriken');pl.level=6;
              pl.bind['naruto-kunai']=1;pl.arrange();
              card=G.LevelUp.offer(pl).find(card=>later.some(id=>id!==learned&&card.key==='new:'+id));
              assert(card,'Missing guaranteed level 6 skill with full slots: '+mon.dex);
              assert(card.apply(pl)!==false&&pl.slots.length===4,'Full slot replacement failed: '+mon.dex);
              assert(privateIds.every(id=>pl.hasMove(id)),'Replacement removed an identity skill: '+mon.dex);
              rosters.push({dex:mon.dex,skills:privateIds});
            }
            result.rosters=rosters;
            const S=G.NarutoSupport;
            assert(S&&G.NarutoOffense,'New technique modules were not loaded');
            setup(30003);pl.hp=pl.maxHp-1;cast('naruto-medical-heal');
            assert(pl.hp===pl.maxHp,'Medical healing overflowed or failed');
            G.Combat.clearFields();
            assert(!S.canCast(pl,G.Moves.instance('naruto-medical-heal')),'Full-health healing can still be cast');
            setup(30003);pl.hp=pl.maxHp*.2;
            const beforeRegen=pl.hp;cast('naruto-regeneration');
            assert(pl.hp===beforeRegen,'Regeneration was an instant burst');
            step(2.1);assert(pl.hp>beforeRegen&&pl.hp<=pl.maxHp,'Regeneration did not heal periodically');
            step(30);const expiredHp=pl.hp;step(2);
            assert(pl.hp===expiredHp,'Regeneration survived its duration');
            result.healing='bounded, periodic, expires, full-health suppressed';

            setup(30002,[[200,0]]);cast('naruto-sharingan');
            const hp=pl.hp;pl.hurt(10);
            assert(pl.hp===hp,'Sharingan failed to avoid one hit');
            pl.invuln=0;pl.hurt(10);
            assert(pl.hp<hp,'Sharingan avoided more than one hit');
            const empowered=S.takeAttackBonus(pl),consumed=S.takeAttackBonus(pl);
            assert(empowered>1&&consumed===1,'Sharingan next-attack bonus did not consume exactly once');
            // Exercise actual dispatch consumption too, instead of only the helper.
            setup(30002,[[180,0]]);cast('naruto-sharingan');cast('naruto-fireball');
            assert(S.takeAttackBonus(pl)===1,'Offensive cast failed to consume Sharingan bonus');
            result.sharingan='one dodge and one offensive bonus';

            let e=setup(30005,[[80,0],[2000,0]]);cast('naruto-byakugan');
            assert(S.precisionMultiplier(pl,e[0])>1&&S.precisionMultiplier(pl,e[1])===1,'Byakugan range mismatch');
            G.World.isWall=x=>x>30&&x<50;G.World.projectileBlock=G.World.isWall;
            assert(S.precisionMultiplier(pl,e[0])===1,'Byakugan precision damage passed through a wall');
            G.World.isWall=()=>false;G.World.projectileBlock=()=>false;
            step(30);assert(S.precisionMultiplier(pl,e[0])===1,'Byakugan did not expire');
            result.byakugan='range, line of sight, expiration';

            setup(30006,[[200,0]]);const atk=pl.atk,spd=pl.spd;cast('naruto-gates');
            assert(pl.atk>atk&&pl.spd>spd,'Eight Gates failed to raise attack and speed');
            pl.atkMul*=1.2;G.Combat.clearFields();
            assert(close(pl.atk,atk*1.2)&&close(pl.spd,spd),'Gates cleanup erased a concurrent upgrade or retained buffs');
            pl.atkMul=1;cast('naruto-gates');step(5.2);
            assert(close(pl.atk,atk)&&pl.spd<spd,'Eight Gates did not transition into temporary fatigue');
            // Both active phase and fatigue must eventually finish without permanent stat changes.
            step(30);assert(close(pl.atk,atk)&&close(pl.spd,spd),'Gates or fatigue persisted after expiration');
            result.gates='temporary buffs, concurrent upgrade retained, fatigue expires';

            setup(30007,[[200,0]]);cast('naruto-sand-shield');const shieldHp=pl.hp;
            const ttl=S.geteffects().find(effect=>effect.mode==='sand-shield').age;
            assert(!cast('naruto-sand-shield')&&S.geteffects().find(effect=>effect.mode==='sand-shield').age===ttl,'Active sand shield refreshed on recast');
            pl.hurt(5);assert(pl.hp===shieldHp,'Sand shield did not absorb damage');
            pl.invuln=0;pl.hp=100000;pl.hurt(1000);
            assert(pl.hp<100000,'Sand shield had infinite absorption');
            pl.invuln=0;const depletedHp=pl.hp;pl.hurt(10);
            assert(pl.hp<depletedHp,'Depleted sand shield kept blocking');
            assert(!cast('naruto-sand-shield'),'Broken sand shield bypassed break lock');
            setup(30007,[[200,0]]);cast('naruto-sand-shield');step(30);
            pl.invuln=0;const expiredShieldHp=pl.hp;pl.hurt(5);
            assert(pl.hp<expiredShieldHp,'Sand shield never expired');
            result.sandShield='finite absorption and expiration';

            setup(30004,[[200,0]]);assert(cast('naruto-earth-wall'),'Earth wall failed on legal empty ground');
            const wall=S.geteffects().find(effect=>effect.mode==='earth-wall');
            const projectile=(friendly,y=wall.y)=>G.Projectiles.spawn({x:wall.x-25,y,px:wall.x+25,py:y,friendly,r:3,dmg:5,hits:new Set(),mtype:'normal'});
            const hostile=projectile(false),friendly=projectile(true),outside=projectile(false,wall.y+wall.width);
            G.Combat.resolve(.01,pl,time);
            assert(!G.Projectiles.all().includes(hostile)&&G.Projectiles.all().includes(friendly)&&G.Projectiles.all().includes(outside),'Earth wall projectile interception geometry or allegiance');
            const walker=new G.Enemy({dex:19,hp:100000,spd:0,dmg:0,xp:0,behavior:'chase'},wall.x+2,wall.y,{hp:1,spd:1,dmg:1});
            G.EnemyMgr.add(walker);G.EnemyMgr.rebuildGrid();const oldX=walker.x;step(.1);
            assert(walker.x>oldX,'Earth wall did not repel an overlapping ordinary enemy');
            assert(G.World.isFree(wall.x,wall.y,10,true),'Earth wall permanently changed map collision');
            step(4);G.Projectiles.clear();const expiredWallShot=projectile(false);G.Combat.resolve(.01,pl,time);
            assert(G.Projectiles.all().includes(expiredWallShot),'Expired earth wall continued blocking');
            result.earthWall='swept hostile interception, friendly and outside pass, repel, expiration';

            // No support state may survive owner death or scene changes.
            setup(30003);pl.hp=pl.maxHp*.2;cast('naruto-regeneration');
            pl.dead=true;const deadHp=pl.hp;step(3);assert(pl.hp===deadHp,'Dead owner kept regenerating');
            pl.dead=false;G.Combat.clearFields();assert(S.geteffects().length===0,'Support fields survived scene cleanup');
            e=setup(30006,[[75,0],[88,24],[88,-24],[420,0]]);
            cast('naruto-lotus');step(2);
            let damage=e.map(loss);
            assert(damage.slice(0,3).every(value=>value>0)&&damage[3]===0,'Lotus landing did not hit a local crowd');
            assert(damage[0]>damage[1]&&damage[1]===damage[2],'Lotus main-target/landing damage allocation');
            const lotusDamage=[...damage];step(2);
            assert(e.every((enemy,index)=>loss(enemy)===lotusDamage[index]),'Lotus landing damage repeated');
            const lotus=G.Moves.instance('naruto-lotus'),lotusBase=lotus.dmg*pl.atk*G.Types.mult(lotus.type,e[0].types)*G.Weather.mult(lotus.type);
            assert(lotusDamage[0]===Math.round(lotusBase*.7)&&lotusDamage[1]===Math.round(lotusBase*.3),'Lotus exceeded main/landing budgets');
            e=setup(30006,[[75,0]]);e[0].boss=true;cast('naruto-lotus');step(.4);
            assert(!e[0].jumpLift&&e[0].slow<=.3,'Lotus launched or hard-locked a boss');
            result.lotus=lotusDamage;

            e=setup(30007,[[90,0],[100,24],[100,-24]]);cast('naruto-sand-coffin');step(2.5);
            damage=e.map(loss);
            assert(damage.filter(value=>value>0).length===1,'Sand coffin affected multiple targets');
            e=setup(30007,[[90,0],[100,24]]);cast('naruto-sand-coffin');e[0].dead=true;step(2.5);
            assert(loss(e[1])===0,'Dead coffin target transferred damage to a new enemy');
            e=setup(30007,[[90,0]]);e[0].boss=true;cast('naruto-sand-coffin');step(.2);
            assert(e[0].slow<=.35,'Sand coffin did not reduce boss control');
            result.sandCoffin='one capture; dead target drops';

            e=setup(30008,[[55,0],[100,20],[100,-20]]);
            e[1].golden=true;e[1].elite=true;cast('naruto-itachi');step(.12);
            assert(e.every(enemy=>loss(enemy)===0),'Tsukuyomi dealt damage before the wind-up');
            step(2);damage=e.map(loss);
            assert(damage[1]>0&&damage[0]===0&&damage[2]===0,'Tsukuyomi did not select exactly one preferred elite');
            result.tsukuyomi=damage;

            e=setup(30008,[[100,0],[120,20],[120,-20],[450,0]]);
            cast('naruto-black-flames');step(2);damage=e.map(loss);
            assert(damage.slice(0,3).every(value=>value>0)&&damage[3]===0,'Black flame spread was not bounded local AoE');
            step(30);const burned=e.map(loss);step(2);
            assert(e.every((enemy,index)=>loss(enemy)===burned[index]),'Black flames survived expiration');
            const flames=G.Moves.instance('naruto-black-flames');
            const tickCount=Math.floor(flames.fieldDuration/flames.fieldTick+1e-8);
            const tickDamage=Math.round(flames.dmg*pl.atk*G.Types.mult(flames.type,e[0].types)*G.Weather.mult(flames.type));
            assert(burned.slice(0,3).every(value=>value===tickDamage*tickCount),'Black flame tick duplicated its damage budget');
            e=setup(30008,[[100,0]]);cast('naruto-black-flames');cast('naruto-black-flames');cast('naruto-black-flames');
            assert(G.NarutoOffense.effects.filter(effect=>effect.kind==='black-flames').length===2,'Black flames did not enforce two-field cap');
            e=setup(30008,[[100,0],[120,0]]);
            G.World.isWall=x=>x>60&&x<80;G.World.projectileBlock=G.World.isWall;
            cast('naruto-black-flames');step(2);
            assert(e.every(enemy=>loss(enemy)===0),'Black flames acquired targets through a wall');
            G.World.isWall=()=>false;G.World.projectileBlock=()=>false;
            e=setup(30008,[[100,0]]);cast('naruto-black-flames');step(.1);
            const aliveLoss=loss(e[0]);pl.dead=true;step(2);
            assert(loss(e[0])===aliveLoss,'Dead owner kept damaging with black flames');
            pl.dead=false;G.Combat.clearFields();assert(G.NarutoOffense.effects.length===0,'Offense fields survived cleanup');
            result.blackFlames='local spread, wall blocking, finite lifetime, dead-owner cleanup';
            for(const dex of [1,20001]) {
              setup(30003);pl.mon=G.DEX_BY[dex];pl.dex=dex;pl.moves=[];pl.slots=[];pl.addMove(pl.mon.start);
              assert(!S.canCast(pl,G.Moves.instance('naruto-gates')),'Non-ninja received Naruto support buffs: '+dex);
              pl.invuln=0;const baseline=pl.hp;
              const factor=pl.activeGroup().some(move=>move.kind==='melee')?.75:1;
              pl.hurt(10);assert(close(baseline-pl.hp,Math.max(1,10*(1-pl.reduction)*factor)),'Player hurt wrapper changed ordinary damage: '+dex);
            }
            result.otherFranchises='Pokemon and Digimon support rejection and unchanged damage';
            return result;
          } finally {G.Combat.clearFields();Object.assign(G.World,saved);pl.dead=false;}
        }''')
        page.evaluate('''() => {
          G.Game.quit();G.Flow.goMenu();
          const perks=G.Upgrades.perks,pick=G.U.pick;
          try {
            G.Upgrades.perks=(...args)=>({...perks(...args),startMoves:2});
            for(const mon of G.Naruto.records.values()) {
              const privateIds=[...(G.NarutoSkillCatalog.extraPools.get(mon.dex)||[])];
              G.U.pick=list=>list.find(id=>privateIds.includes(id))||pick(list);
              G.Naruto.choose(mon.dex);G.Flow.play();
              const ids=G.Game.player.moves.map(move=>move.id);
              if(ids.length!==2||ids.some(id=>![mon.start,'naruto-kunai','naruto-shuriken'].includes(id)))
                throw Error('Extra starting-move perk bypassed training: '+mon.dex);
              G.Game.quit();G.Flow.goMenu();
            }
          }finally{G.Upgrades.perks=perks;G.U.pick=pick;G.Game.quit();G.Flow.goMenu();}
        }''')
        # A full Flow.play() start for every identity catches sprite/start-move integration.
        starts = []
        for dex in range(30001, 30009):
            value = page.evaluate('''dex=>{
              G.Game.quit();G.Flow.goMenu();G.Naruto.choose(dex);G.Flow.play();
              const player=G.Game.player;
              return {dex:player.dex,start:player.moves[0].id,hp:player.hp,state:G.Game.state};
            }''', dex)
            assert value['dex'] == dex and value['hp'] > 0 and value['state'] == 'playing', value
            page.wait_for_timeout(120)
            page.evaluate('G.Game.togglePause()')
            starts.append(value)
        assert not errors, errors
        assert not missing, missing
        print(json.dumps({'combat':report,'starts':starts,'javascript_errors':errors,'missing_assets':missing},ensure_ascii=True))
    finally:
        browser.close()
