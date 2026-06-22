import { useProjectStore } from './store/useProjectStore';
import Step1_Script from './components/Step1_Script';
import Step2_Images from './components/Step2_Images';
import Step3_Voice from './components/Step3_Voice';
import Step4_Template from './components/Step4_Template';
import ResultView from './components/ResultView';

const STEPS = [
  { id: 1, name: '대본 편집' },
  { id: 2, name: '이미지 선택' },
  { id: 3, name: '목소리 선택' },
  { id: 4, name: '스타일 선택' },
];

const LOADING = {
  analyzing:       { tint: 'border-t-indigo-600', text: '블로그를 분석하고 대본을 만드는 중이에요' },
  processing_tts:  { tint: 'border-t-emerald-500', text: '선택한 목소리로 음성을 입히는 중이에요' },
  rendering_video: { tint: 'border-t-indigo-600', text: '이미지·자막·음성을 합쳐 영상을 만드는 중이에요' },
};

function App() {
  const { currentStep, blogUrl, setBlogUrl, statusMode, handleStartAnalysis } = useProjectStore();
  const load = LOADING[statusMode];

  return (
    <div className="min-h-screen bg-[#f7f8fa] text-slate-900 flex antialiased">

      {/* 전체 화면 로딩 오버레이 */}
      {load && (
        <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-white/80 backdrop-blur-sm text-center px-6">
          <div className={`w-14 h-14 rounded-full border-4 border-slate-200 ${load.tint} animate-spin mb-5`} />
          <p className="font-bold text-lg text-slate-800">{load.text}</p>
          <p className="text-sm text-slate-400 mt-1">잠시만 기다려 주세요…</p>
        </div>
      )}

      {/* 좌측 사이드바 */}
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col p-5 shrink-0">
        <div className="flex items-center gap-2.5 mb-9 px-1">
          <span className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-black text-sm">S</span>
          <span className="font-black tracking-tight text-lg text-slate-900">SuperShorts</span>
        </div>

        <p className="text-[11px] font-bold text-slate-400 px-2 mb-3 tracking-wide">제작 단계</p>
        <nav className="flex flex-col gap-1.5">
          {STEPS.map((st) => {
            const active = currentStep === st.id;
            const done = currentStep > st.id;
            return (
              <div key={st.id}
                className={`flex items-center gap-3 px-3 py-3 rounded-xl text-sm font-bold transition-all ${
                  active ? 'bg-indigo-50 text-indigo-700'
                  : done ? 'text-slate-700'
                  : 'text-slate-400'
                }`}>
                <span className={`w-6 h-6 rounded-full flex items-center justify-center text-[11px] font-bold shrink-0 ${
                  active ? 'bg-indigo-600 text-white'
                  : done ? 'bg-indigo-100 text-indigo-600'
                  : 'bg-slate-100 text-slate-400'
                }`}>
                  {done ? '✓' : st.id}
                </span>
                {st.name}
              </div>
            );
          })}
        </nav>

        <div className="mt-auto rounded-xl bg-slate-50 border border-gray-200 p-4">
          <p className="text-xs font-bold text-slate-700 mb-1">네이버 블로그 → 쇼츠</p>
          <p className="text-[11px] text-slate-400 leading-relaxed">링크 하나로 9:16 영상을 자동으로 만들어요.</p>
        </div>
      </aside>

      {/* 메인 영역 */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 border-b border-gray-200 flex items-center justify-between px-8 bg-white">
          <span className="text-sm font-medium text-slate-400">
            대시보드 <span className="text-slate-300">/</span> <span className="text-slate-700 font-bold">새 영상 만들기</span>
          </span>
          <div className="w-9 h-9 rounded-full bg-indigo-600 flex items-center justify-center font-bold text-xs text-white">나</div>
        </header>

        <main className="flex-1 p-8 overflow-y-auto w-full max-w-5xl mx-auto">
          {currentStep === 0 && !statusMode && (
            <div className="flex flex-col items-center justify-center min-h-[68vh] text-center max-w-2xl mx-auto animate-fade-in">
              <span className="text-xs font-bold text-indigo-600 tracking-wide bg-indigo-50 px-3.5 py-1.5 rounded-full mb-5">
                링크만 넣고 바로 시작
              </span>
              <h2 className="text-4xl font-black text-slate-900 tracking-tight mb-3">
                블로그 주소 하나로<br />숏폼 영상을 만들어요
              </h2>
              <p className="text-slate-500 mb-9">네이버 블로그 링크를 붙여넣으면 대본·이미지·자막까지 자동으로 준비됩니다.</p>

              <div className="w-full bg-white border border-gray-200 rounded-2xl p-3 shadow-sm flex items-center gap-2 focus-within:ring-2 focus-within:ring-indigo-500/30 focus-within:border-indigo-400 transition-all">
                <span className="pl-3 text-slate-300 text-lg">🔗</span>
                <input
                  type="url"
                  className="flex-1 bg-transparent py-3 text-[15px] text-slate-900 placeholder-slate-400 focus:outline-none"
                  placeholder="네이버 블로그 링크를 붙여넣어 주세요"
                  value={blogUrl}
                  onChange={(e) => setBlogUrl(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleStartAnalysis()}
                />
                <button
                  onClick={handleStartAnalysis}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold px-6 py-3 rounded-xl transition-all shrink-0 cursor-pointer"
                >
                  시작하기
                </button>
              </div>
              <p className="text-xs text-slate-400 mt-4">예: https://blog.naver.com/아이디/포스트번호</p>
            </div>
          )}

          {currentStep === 1 && <Step1_Script />}
          {currentStep === 2 && <Step2_Images />}
          {currentStep === 3 && <Step3_Voice />}
          {currentStep === 4 && <Step4_Template />}
          {currentStep === 5 && <ResultView />}
        </main>
      </div>
    </div>
  );
}

export default App;
