from pathlib import Path

p = Path("buildsrc/app/src/main/assets/index.html")
s = p.read_text()

s = s.replace(
    "Monitoring your ESP32 sensors for motion.",
    "Monitoring PIR motion and vibration/tamper sensors."
)

s = s.replace(
    '<div class="card metric"><div class="icon">◉</div><div class="label">PIR SENSOR</div><div id="pirValue" class="value">Ready</div><div id="pirMini" class="mini">Waiting for motion</div></div>\n        <div class="card metric"><div class="icon">☼</div><div class="label">LIGHTING</div>',
    '<div class="card metric"><div class="icon">◉</div><div class="label">PIR SENSOR</div><div id="pirValue" class="value">Ready</div><div id="pirMini" class="mini">Waiting for motion</div></div>\n        <div class="card metric"><div class="icon">≋</div><div class="label">VIBRATION / TAMPER</div><div id="vibrationValue" class="value">Ready</div><div id="vibrationMini" class="mini">Monitoring tampering</div></div>\n        <div class="card metric"><div class="icon">☼</div><div class="label">LIGHTING</div>'
)

s = s.replace(
    '<div class="grid">\n        <button class="btn card" onclick="capture(\'CAPTURE\')">📷 Capture</button>\n        <button class="btn card" onclick="capture(\'CAPTURE_FLASH\')">⚡ Capture + Flash</button>\n      </div>',
    '<div class="grid">\n        <button class="btn card" onclick="publishCommand(\'SILENCE_ALARM\')">🔇 Silence Alarm</button>\n        <button class="btn card" onclick="publishCommand(\'PANIC_ALARM\')">🚨 Panic Alarm</button>\n        <button class="btn card" onclick="capture(\'CAPTURE\')">📷 Capture</button>\n        <button class="btn card" onclick="capture(\'CAPTURE_FLASH\')">⚡ Capture + Flash</button>\n        <button class="btn card" onclick="publishCommand(\'STATUS_REQUEST\')">↻ Refresh Device Status</button>\n      </div>',
    1
)

s = s.replace(
    '<div class="field"><label>COMMAND TOPIC (OPTIONAL)</label><input id="settingCommandTopic" class="input" placeholder="home/security/commands" /></div>',
    '<div class="field"><label>COMMAND TOPIC</label><input id="settingCommandTopic" class="input" value="home/security/commands" /></div>\n        <div class="field"><label>DEVICE STATUS TOPIC</label><input id="settingStatusTopic" class="input" value="home/security/status" /></div>'
)

s = s.replace(
    '<button class="btn danger" style="width:100%" onclick="testAlert()">Generate test motion alert</button>\n        <div class="help">The test event is labelled TEST so it cannot be confused with a real PIR trigger.</div>',
    '<button class="btn danger" style="width:100%" onclick="testAlert()">Generate test motion alert</button>\n        <button class="btn danger" style="width:100%;margin-top:10px" onclick="testVibrationAlert()">Generate test vibration/tamper alert</button>\n        <div class="help">TEST events are labelled so they cannot be confused with real PIR or vibration sensor triggers.</div>'
)

s = s.replace(
    "commandTopic: '',\n  cameraUrl: ''",
    "commandTopic: 'home/security/commands',\n  statusTopic: 'home/security/status',\n  cameraUrl: ''"
)

s = s.replace(
    "$('armedSub').textContent = armed ? 'Monitoring your ESP32 sensors for motion.' : 'Monitoring paused locally.';",
    "$('armedSub').textContent = armed ? 'Monitoring PIR motion and vibration/tamper sensors.' : 'Monitoring paused. Sensors will not trigger the alarm.';"
)

s = s.replace(
    "$('settingCommandTopic').value = settings.commandTopic || '';",
    "$('settingCommandTopic').value = settings.commandTopic || defaults.commandTopic;\n  $('settingStatusTopic').value = settings.statusTopic || defaults.statusTopic;"
)

a = s.index("function toggleArmed(){")
b = s.index("\n}\n\nfunction mqttUrl()", a) + 2
s = s[:a] + """function toggleArmed(){
  const target = !armed;
  if(!client || !connected){ toast('MQTT is not connected'); return; }
  publishCommand(target ? 'ARM' : 'DISARM');
  armed = target;
  saveJSON('hg_armed', armed);
  syncUI();
  if(!armed){
    $('alarmValue').textContent='Off';
    $('pirValue').textContent='Disarmed';
    $('vibrationValue').textContent='Disarmed';
  }
}
""" + s[b:]

s = s.replace(
    "const topics = Array.from(new Set([settings.alertTopic, 'home/security/#']));",
    "const topics = Array.from(new Set([settings.alertTopic, settings.statusTopic, 'home/security/#']));"
)

s = s.replace(
    """      if(topic===settings.alertTopic || topic.startsWith('home/security/')){
        processAlert(text, false);
      }""",
    """      if(topic===settings.statusTopic){
        processDeviceStatus(text);
        return;
      }
      if(topic===settings.alertTopic){
        processAlert(text, false);
      }"""
)

s = s.replace(
    "if(up.includes('MOTION')) base.type='MOTION'; else if(up) base.type=up;",
    "if(up.includes('VIBRATION') || up.includes('TAMPER')) base.type='TAMPER'; else if(up.includes('MOTION')) base.type='MOTION'; else if(up) base.type=up;"
)

a = s.index("function processAlert(payload, isTest){")
b = s.index("\n}\n\nfunction mqttRoundTripTest()", a) + 2
s = s[:a] + r"""function processAlert(payload, isTest){
  if(!armed && !isTest) return;
  const event=parseAlert(payload);
  event.test=!!isTest;
  event.timestamp=Date.now();
  if(event.cameraUrl) settings.cameraUrl=event.cameraUrl;

  const isTamper = ['TAMPER','VIBRATION','SHOCK'].includes(event.type);
  const eventName = isTamper ? 'Vibration / tamper detected' : 'Motion detected';

  alerts.unshift(event);
  alerts=alerts.slice(0,100);
  saveJSON('hg_alerts',alerts);

  if(isTamper){
    $('vibrationValue').textContent='TAMPER';
    $('vibrationMini').textContent=isTest?'Test trigger':'Vibration detected now';
  } else {
    $('pirValue').textContent='MOTION';
    $('pirMini').textContent=isTest?'Test trigger':'Triggered now';
  }

  $('lightValue').textContent=event.environment.charAt(0)+event.environment.slice(1).toLowerCase();
  $('alarmValue').textContent=event.alarm==='OFF'?'Off':'ACTIVE';
  $('cameraValue').textContent='Capturing…';
  $('lastEventTitle').textContent=(isTest?'TEST · ':'')+eventName;
  $('lastEventDetails').textContent=event.environment+' environment · Alarm '+event.alarm;
  $('lastEventTime').textContent=shortTime(event.timestamp);
  $('eventDot').classList.add('alert');

  $('alertBannerTitle').textContent=(isTest?'Test alert':'Security alert')+' — '+eventName;
  $('alertBannerText').textContent=event.environment+' environment · '+nowText(event.timestamp);
  $('alertBanner').classList.add('show');
  clearTimeout(lastAlertTimer);
  lastAlertTimer=setTimeout(()=>$('alertBanner').classList.remove('show'),12000);

  vibrateAlert();
  playTone();
  androidNotify(isTest?'HomeGuard test alert':'HomeGuard security alert', eventName+' · '+event.environment);
  renderHistory();

  setTimeout(()=>{ if(armed) $('alarmValue').textContent='Standby'; },10000);
  if(isTamper){
    setTimeout(()=>{ $('vibrationValue').textContent=armed?'Ready':'Disarmed'; $('vibrationMini').textContent=armed?'Monitoring tampering':'System disarmed'; },3500);
  } else {
    setTimeout(()=>{ $('pirValue').textContent=armed?'Ready':'Disarmed'; $('pirMini').textContent=armed?'Waiting for motion':'System disarmed'; },3500);
  }
  if(settings.cameraUrl){ setTimeout(()=>refreshCamera(false),1600); }
}

function processDeviceStatus(payload){
  try{
    const st=JSON.parse(payload);
    if(typeof st.armed==='boolean'){
      armed=st.armed;
      saveJSON('hg_armed',armed);
    }
    if(st.alarm!==undefined){
      const alarm=String(st.alarm).toUpperCase();
      $('alarmValue').textContent=(alarm==='ACTIVE'||alarm==='ON')?'ACTIVE':'Standby';
    }
    if(st.pir!==undefined){
      const pir=Number(st.pir);
      $('pirValue').textContent=armed?(pir?'MOTION':'Ready'):'Disarmed';
      $('pirMini').textContent=armed?(pir?'Motion currently detected':'Waiting for motion'):'System disarmed';
    }
    if(st.vibration!==undefined){
      const vib=Number(st.vibration);
      $('vibrationValue').textContent=armed?(vib?'TAMPER':'Ready'):'Disarmed';
      $('vibrationMini').textContent=armed?(vib?'Vibration currently detected':'Monitoring tampering'):'System disarmed';
    }
    syncUI();
    $('lastEventDetails').textContent='Device status synchronized from ESP32.';
  }catch(e){}
}
""" + s[b:]

s = s.replace(
    "function testAlert(){ processAlert('MOTION_DARK', true); toast('Test alert generated'); }\n\nfunction capture(mode){",
    """function testAlert(){ processAlert('MOTION_DARK', true); toast('Test motion alert generated'); }
function testVibrationAlert(){ processAlert('{"type":"TAMPER","environment":"DARK","alarm":"ACTIVE"}', true); toast('Test vibration alert generated'); }

function publishCommand(command){
  if(!client || !connected){ toast('MQTT is not connected'); return; }
  const topic=settings.commandTopic || defaults.commandTopic;
  client.publish(topic, command, {qos:0}, err=>{
    if(err){ toast(command+' command failed'); return; }
    if(command==='DISARM' || command==='SILENCE_ALARM') $('alarmValue').textContent='Off';
    if(command==='PANIC_ALARM') $('alarmValue').textContent='ACTIVE';
    toast(command.replaceAll('_',' ')+' sent');
  });
}

function capture(mode){"""
)

s = s.replace(
    "commandTopic:$('settingCommandTopic').value.trim()",
    "commandTopic:$('settingCommandTopic').value.trim()||defaults.commandTopic,\n    statusTopic:$('settingStatusTopic').value.trim()||defaults.statusTopic"
)

s = s.replace(
    "${a.test?'TEST · ':''}${escapeHtml(a.type||'MOTION')}",
    "${a.test?'TEST · ':''}${escapeHtml((a.type==='TAMPER'||a.type==='VIBRATION')?'VIBRATION / TAMPER':(a.type||'MOTION'))}"
)

s = s.replace(
    "if(force) toast('MQTT connected + subscribed');",
    "if(force) toast('MQTT connected + subscribed');\n          setTimeout(()=>publishCommand('STATUS_REQUEST'),250);"
)

p.write_text(s)
