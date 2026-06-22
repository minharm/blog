import { useState } from 'react';
import { useProjectStore } from '../store/useProjectStore';

export default function Step4_Template() {
  const [activeTab, setActiveTab] = useState('recommended'); 
  const { projectData, setSelectedTemplate, fxSettings, toggleFxSetting, setBgmTrack, customTemplate, updateCustomTemplate, handleFinalVideoGeneration, setCurrentStep } = useProjectStore();

  return (
    <div className="animate-fade-in grid grid-cols-1 lg:grid-cols-12 gap-8">
      
      {/* 🛠️ 좌측 섹션 */}
      <div className="lg:col-span-8 flex flex-col gap-6">
        <div className="flex justify-between items-center">
          <button onClick={() => setCurrentStep(3)} className="text-sm text-slate-500 hover:text-slate-300 font-bold">← 이전으로</button>
          <span className="text-xs font-bold text-blue-400 uppercase">Step 4</span>
        </div>
        <h3 className="text-2xl font-black text-white">영상 스타일 및 효과 장착</h3>

        <div className="flex border-b border-slate-800 text-sm font-bold">
          <button onClick={() => setActiveTab('recommended')} className={`px-6 py-2.5 transition-all ${activeTab === 'recommended' ? 'text-blue-500 border-b-2 border-b-blue-500' : 'text-slate-500'}`}>추천 템플릿</button>
          <button onClick={() => setActiveTab('my_template')} className={`px-6 py-2.5 transition-all ${activeTab === 'my_template' ? 'text-blue-500 border-b-2 border-b-blue-500' : 'text-slate-500'}`}>내 템플릿</button>
        </div>

        {activeTab === 'recommended' ? (
          <div className="grid grid-cols-3 gap-4">
            {[
              { id: 'basic', name: '정보성 기본', desc: '깔끔하고 정갈한 클래식 스타일' },
              { id: 'dark', name: '정보성 다크', desc: '힙한 반투명 다크 컨테이너 핏' },
              { id: 'mint', name: '바이럴 민트', desc: '트렌디한 민트 스포트라이트바 연출' }
            ].map((tmpl) => (
              <div key={tmpl.id} onClick={() => setSelectedTemplate(tmpl.id)} className={`p-4 rounded-xl border cursor-pointer transition-all ${projectData.selectedTemplate === tmpl.id ? 'bg-blue-600/10 border-blue-500' : 'bg-slate-900 border-slate-800'}`}>
                <span className="text-xs font-black text-white block mb-1">{tmpl.name}</span>
                <span className="text-[10px] text-slate-500">{tmpl.desc}</span>
              </div>
            ))}
          </div>
        ) : (
          <div onClick={() => setSelectedTemplate('custom')} className={`p-6 rounded-2xl border-2 border-dashed border-slate-800 flex items-center justify-center text-xs font-bold cursor-pointer transition-all ${projectData.selectedTemplate === 'custom' ? 'bg-blue-600/5 border-blue-500 text-blue-400' : 'text-slate-500 hover:border-slate-700'}`}>
            ✨ 우측 서체/색상 커스텀 필터가 영상에 그대로 전사 적용됩니다 (선택 활성화)
          </div>
        )}

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-col gap-4 shadow-xl">
          <h4 className="text-sm font-black text-slate-300 border-b border-slate-800 pb-2">🎵 사운드 시스템 및 부가 연출 제어</h4>
          
          <div className="flex items-center justify-between bg-slate-950 p-3.5 rounded-xl border border-slate-800/60">
            <div>
              <span className="text-xs font-bold text-white block">자동 효과음</span>
              <span className="text-[10px] text-slate-500">강조 포인트 자막 구간에 효과음을 자동 배치합니다.</span>
            </div>
            <input type="checkbox" checked={fxSettings.autoFx} onChange={() => toggleFxSetting('autoFx')} className="w-4 h-4 accent-blue-500 cursor-pointer" />
          </div>

          <div className="flex items-center justify-between bg-slate-950 p-3.5 rounded-xl border border-slate-800/60">
            <div>
              <span className="text-xs font-bold text-white block">자동 BGM</span>
              <span className="text-[10px] text-slate-500">대본 무드에 어울리는 배경음악을 지능형 자동 믹싱합니다.</span>
            </div>
            <input type="checkbox" checked={fxSettings.autoBgm} onChange={() => toggleFxSetting('autoBgm')} className="w-4 h-4 accent-blue-500 cursor-pointer" />
          </div>

          <div className="flex flex-col gap-2 bg-slate-950 p-3.5 rounded-xl border border-slate-800/60">
            <span className="text-xs font-bold text-white block">BGM 직접 고르기</span>
            <select value={fxSettings.bgmTrack} onChange={(e) => setBgmTrack(e.target.value)} className="w-full bg-slate-900 border border-slate-800 text-xs text-slate-300 p-2 rounded-lg focus:outline-none">
              <option value="track_01">밝고 신나는 비트 트랙 (SaaS 기본형)</option>
              <option value="track_02">잔잔한 브이로그 무드 (안정형)</option>
              <option value="track_03">리뷰 긴박한 일렉트로닉 (바이럴형)</option>
            </select>
          </div>
        </div>
      </div>

      {/* 🎨 우측 섹션: 내 전용 템플릿 커스텀 콘솔 */}
      <div className="lg:col-span-4 bg-slate-900 border border-slate-800 rounded-3xl p-5 shadow-2xl flex flex-col gap-5">
        <div>
          <span className="text-[10px] font-black tracking-widest text-blue-400 bg-blue-500/10 px-2.5 py-1 rounded border border-blue-500/20 uppercase">My Dedicated Template</span>
          <h4 className="text-base font-black text-white mt-2">내 템플릿 제어</h4>
        </div>

        <div className="flex flex-col gap-3.5 text-xs bg-slate-950 p-4 rounded-xl border border-slate-800">
          <div className="flex flex-col gap-1">
            <span className="text-slate-400 font-bold">폰트 스타일</span>
            <select value={customTemplate.fontFamily} onChange={(e) => updateCustomTemplate('fontFamily', e.target.value)} className="bg-slate-900 border border-slate-800 p-2 rounded text-slate-300 focus:outline-none">
              <option value="Pretendard">Pretendard (SaaS 웹 고딕 표준)</option>
              <option value="GmarketSans">Gmarket Sans (볼드형 타이틀 사양)</option>
              <option value="NotoSans">Noto Sans KR (정갈한 기본 고딕)</option>
            </select>
          </div>

          <div className="flex flex-col gap-1">
            <span className="text-slate-400 font-bold">글자 크기 (Size)</span>
            <input type="number" value={customTemplate.fontSize} onChange={(e) => updateCustomTemplate('fontSize', Number(e.target.value))} className="bg-slate-900 border border-slate-800 p-2 rounded text-slate-300 focus:outline-none" />
          </div>

          <div className="flex flex-col gap-1">
            <span className="text-slate-400 font-bold">첫째 줄 글자 색상</span>
            <div className="flex items-center gap-2">
              <input type="color" value={customTemplate.colorLine1} onChange={(e) => updateCustomTemplate('colorLine1', e.target.value)} className="bg-transparent w-8 h-8 rounded cursor-pointer" />
              <span className="font-mono text-[11px] text-slate-500 uppercase">{customTemplate.colorLine1}</span>
            </div>
          </div>

          <div className="flex flex-col gap-1">
            <span className="text-slate-400 font-bold">둘째 줄 포인트 색상</span>
            <div className="flex items-center gap-2">
              <input type="color" value={customTemplate.colorLine2} onChange={(e) => updateCustomTemplate('colorLine2', e.target.value)} className="bg-transparent w-8 h-8 rounded cursor-pointer" />
              <span className="font-mono text-[11px] text-slate-500 uppercase">{customTemplate.colorLine2}</span>
            </div>
          </div>

          <div className="flex flex-col gap-1">
            <span className="text-slate-400 font-bold">워터마크 채널명</span>
            <input type="text" value={customTemplate.channelName} onChange={(e) => updateCustomTemplate('channelName', e.target.value)} className="bg-slate-900 border border-slate-800 p-2 rounded text-slate-300 focus:outline-none" />
          </div>
        </div>

        {/* 🎯 [요구사항 반영] 하단 제어부 가시 동선에 맞춰 직관적인 [이전 단계로] 연동 배치 */}
        <div className="flex gap-3 mt-auto w-full">
          <button onClick={() => setCurrentStep(3)} className="w-1/3 bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold py-4 rounded-xl text-center text-sm transition-all">
            이전으로
          </button>
          <button onClick={handleFinalVideoGeneration} className="w-2/3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 text-white font-black py-4 rounded-xl text-center text-sm shadow-xl tracking-wide transition-all">
            🎬 영상 합성 시작
          </button>
        </div>
      </div>

    </div>
  );
}