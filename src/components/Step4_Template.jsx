import { useState } from 'react';
import { useProjectStore, TEMPLATES } from '../store/useProjectStore';

// 카드 안에 들어가는 9:16 폰 목업 미리보기
function PhonePreview({ preview, channel = '@my_shorts' }) {
  const p = preview;
  return (
    <div className="relative w-full aspect-[9/16] rounded-xl overflow-hidden" style={{ background: p.bg }}>
      <span className="absolute top-2 left-1/2 -translate-x-1/2 text-[8px] font-bold opacity-50" style={{ color: '#fff' }}>{channel}</span>
      {/* 가운데 이미지 자리 표시 */}
      <div className="absolute inset-x-3 top-1/4 bottom-1/4 rounded-md bg-white/10" />
      {/* 하단 자막바 */}
      <div className="absolute left-2 right-2 bottom-3 rounded-md px-2 py-1.5 text-center" style={{ background: p.barBg }}>
        <div className="text-[9px] font-black leading-tight" style={{ color: p.title }}>주말 가볼 만한 곳</div>
        <div className="text-[10px] font-black leading-tight" style={{ color: p.point }}>의왕 어드벤처</div>
      </div>
    </div>
  );
}

export default function Step4_Template() {
  const [tab, setTab] = useState('gallery');
  const { projectData, setSelectedTemplate, fxSettings, toggleFxSetting, setBgmTrack, customTemplate, updateCustomTemplate, handleFinalVideoGeneration, setCurrentStep } = useProjectStore();
  const isCustom = projectData.selectedTemplate === 'custom';

  return (
    <div className="animate-fade-in">
      <button onClick={() => setCurrentStep(3)} className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-800 font-bold mb-4 transition-colors">← 이전</button>
      <div className="flex items-center gap-2 mb-1">
        <span className="text-[11px] font-bold text-indigo-600 bg-indigo-50 px-2.5 py-1 rounded-full">STEP 4</span>
      </div>
      <h3 className="text-2xl font-black text-slate-900">영상 스타일을 골라 주세요</h3>
      <p className="text-slate-500 text-sm mt-1.5 mb-6">대본 분위기에 맞는 자막 스타일이에요. 미리보기로 확인하고 선택하세요.</p>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-7">
        {/* 좌측: 템플릿 갤러리 + 사운드 */}
        <div className="lg:col-span-8 flex flex-col gap-6">
          <div className="flex gap-1 border-b border-gray-200 text-sm font-bold">
            <button onClick={() => setTab('gallery')} className={`px-4 py-2.5 -mb-px transition-all ${tab === 'gallery' ? 'text-indigo-600 border-b-2 border-indigo-600' : 'text-slate-400 hover:text-slate-600'}`}>추천 템플릿</button>
            <button onClick={() => setTab('custom')} className={`px-4 py-2.5 -mb-px transition-all ${tab === 'custom' ? 'text-indigo-600 border-b-2 border-indigo-600' : 'text-slate-400 hover:text-slate-600'}`}>나만의 템플릿</button>
          </div>

          {tab === 'gallery' ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              {TEMPLATES.map((t) => {
                const sel = projectData.selectedTemplate === t.id;
                return (
                  <button key={t.id} onClick={() => setSelectedTemplate(t.id)}
                    className={`text-left rounded-2xl border p-2.5 transition-all ${sel ? 'border-indigo-500 ring-2 ring-indigo-500/20 bg-indigo-50/40' : 'border-gray-200 bg-white hover:border-gray-300'}`}>
                    <div className="relative">
                      <PhonePreview preview={t.preview} channel={customTemplate.channelName ? `@${customTemplate.channelName}` : '@my_shorts'} />
                      {t.badge && <span className="absolute top-1.5 left-1.5 text-[9px] font-black text-white bg-black/55 px-1.5 py-0.5 rounded">{t.badge}</span>}
                      {sel && <span className="absolute top-1.5 right-1.5 w-5 h-5 rounded-full bg-indigo-600 text-white text-[11px] font-bold flex items-center justify-center">✓</span>}
                    </div>
                    <div className="px-1 pt-2.5 pb-1">
                      <span className="text-sm font-bold text-slate-900 block">{t.name}</span>
                      <span className="text-[11px] text-slate-400 leading-snug block mt-0.5">{t.desc}</span>
                    </div>
                  </button>
                );
              })}

              {/* 나만의 템플릿 만들기 카드 */}
              <button onClick={() => { setSelectedTemplate('custom'); setTab('custom'); }}
                className={`rounded-2xl border-2 border-dashed flex flex-col items-center justify-center gap-2 aspect-[9/16] transition-all ${isCustom ? 'border-indigo-400 bg-indigo-50/40' : 'border-gray-300 hover:border-indigo-400'}`}>
                <span className="text-2xl text-slate-300">＋</span>
                <span className="text-xs font-bold text-slate-500 text-center px-3">나만의 템플릿<br />만들기</span>
              </button>
            </div>
          ) : (
            <CustomPanel {...{ isCustom, setSelectedTemplate, customTemplate, updateCustomTemplate }} />
          )}

          {/* 폰트 선택 (모든 템플릿에 적용) */}
          <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm flex flex-col gap-2.5">
            <h4 className="text-sm font-black text-slate-700">자막 폰트</h4>
            <select value={customTemplate.fontFamily} onChange={(e) => updateCustomTemplate('fontFamily', e.target.value)}
              className="w-full bg-slate-50 border border-gray-200 text-sm text-slate-700 p-2.5 rounded-lg focus:outline-none focus:border-indigo-400">
              <option value="Pretendard">프리텐다드 (깔끔한 기본)</option>
              <option value="GmarketSans">G마켓 산스 (두꺼운 임팩트)</option>
              <option value="BlackHanSans">검은고딕 (강한 제목용)</option>
              <option value="Jalnan">잘난체 (개성있는 둥근체)</option>
              <option value="NanumGothic">나눔고딕 (단정한 기본)</option>
            </select>
            <p className="text-[11px] text-slate-400 leading-relaxed">선택한 폰트의 파일이 <code className="text-slate-500">backend/static/fonts/</code> 에 있어야 영상에 적용돼요.</p>
          </div>

          {/* 사운드 설정 */}
          <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm flex flex-col gap-3">
            <h4 className="text-sm font-black text-slate-700">배경음악 & 효과음</h4>
            <ToggleRow label="자동 효과음" desc="강조 자막 구간에 효과음을 자동으로 넣어요." on={fxSettings.autoFx} onClick={() => toggleFxSetting('autoFx')} />
            <ToggleRow label="자동 배경음악" desc="대본 분위기에 맞는 BGM을 자동으로 깔아요." on={fxSettings.autoBgm} onClick={() => toggleFxSetting('autoBgm')} />
            <div className="flex flex-col gap-1.5 bg-slate-50 border border-gray-200 p-3 rounded-xl">
              <span className="text-xs font-bold text-slate-700">배경음악 직접 고르기</span>
              <select value={fxSettings.bgmTrack} onChange={(e) => setBgmTrack(e.target.value)}
                className="w-full bg-white border border-gray-200 text-sm text-slate-700 p-2 rounded-lg focus:outline-none focus:border-indigo-400">
                <option value="track_01">밝고 신나는 비트</option>
                <option value="track_02">잔잔한 브이로그 무드</option>
                <option value="track_03">긴박한 일렉트로닉</option>
              </select>
            </div>
          </div>
        </div>

        {/* 우측: 실행 패널 */}
        <div className="lg:col-span-4">
          <div className="sticky top-4 bg-white border border-gray-200 rounded-2xl p-5 shadow-sm flex flex-col gap-4">
            <div>
              <span className="text-[11px] font-bold text-slate-400">선택한 스타일</span>
              <p className="text-lg font-black text-slate-900">
                {isCustom ? '나만의 템플릿' : (TEMPLATES.find(t => t.id === projectData.selectedTemplate)?.name || '정보성')}
              </p>
            </div>
            <div className="rounded-xl bg-slate-50 border border-gray-200 p-3 text-xs text-slate-500 leading-relaxed">
              영상 합성에는 보통 30초~1분쯤 걸려요. 합성 중에는 창을 닫지 말아 주세요.
            </div>
            <div className="flex gap-2.5">
              <button onClick={() => setCurrentStep(3)} className="w-1/3 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold py-3.5 rounded-xl text-sm transition-all">이전</button>
              <button onClick={handleFinalVideoGeneration} className="w-2/3 bg-indigo-600 hover:bg-indigo-700 text-white font-black py-3.5 rounded-xl text-sm transition-all">영상 만들기</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function ToggleRow({ label, desc, on, onClick }) {
  return (
    <div className="flex items-center justify-between bg-slate-50 border border-gray-200 p-3 rounded-xl">
      <div className="min-w-0 pr-3">
        <span className="text-sm font-bold text-slate-800 block">{label}</span>
        <span className="text-[11px] text-slate-400">{desc}</span>
      </div>
      <button onClick={onClick} className={`w-11 h-6 rounded-full transition-colors relative shrink-0 ${on ? 'bg-indigo-600' : 'bg-slate-300'}`} aria-pressed={on}>
        <span className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white transition-transform ${on ? 'translate-x-5' : ''}`} />
      </button>
    </div>
  );
}

function CustomPanel({ isCustom, setSelectedTemplate, customTemplate, updateCustomTemplate }) {
  return (
    <div className={`rounded-2xl border p-5 ${isCustom ? 'border-indigo-400 bg-indigo-50/40' : 'border-gray-200 bg-white'}`}>
      {!isCustom && (
        <button onClick={() => setSelectedTemplate('custom')} className="mb-4 text-xs font-bold text-indigo-600">＋ 이 커스텀 스타일을 영상에 적용하기</button>
      )}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
        <Field label="글자 크기">
          <input type="number" value={customTemplate.fontSize} onChange={(e) => updateCustomTemplate('fontSize', Number(e.target.value))}
            className="w-full bg-white border border-gray-200 p-2.5 rounded-lg text-slate-800 focus:outline-none focus:border-indigo-400" />
        </Field>
        <Field label="채널명 (워터마크)">
          <input type="text" value={customTemplate.channelName} onChange={(e) => updateCustomTemplate('channelName', e.target.value)}
            className="w-full bg-white border border-gray-200 p-2.5 rounded-lg text-slate-800 focus:outline-none focus:border-indigo-400" />
        </Field>
        <Field label="첫째 줄 색상">
          <div className="flex items-center gap-2">
            <input type="color" value={customTemplate.colorLine1} onChange={(e) => updateCustomTemplate('colorLine1', e.target.value)} className="w-9 h-9 rounded cursor-pointer border border-gray-200" />
            <span className="font-mono text-xs text-slate-500 uppercase">{customTemplate.colorLine1}</span>
          </div>
        </Field>
        <Field label="둘째 줄 포인트 색상">
          <div className="flex items-center gap-2">
            <input type="color" value={customTemplate.colorLine2} onChange={(e) => updateCustomTemplate('colorLine2', e.target.value)} className="w-9 h-9 rounded cursor-pointer border border-gray-200" />
            <span className="font-mono text-xs text-slate-500 uppercase">{customTemplate.colorLine2}</span>
          </div>
        </Field>
      </div>
    </div>
  );
}

function Field({ label, children }) {
  return (
    <div className="flex flex-col gap-1.5">
      <span className="text-slate-500 font-bold text-xs">{label}</span>
      {children}
    </div>
  );
}
