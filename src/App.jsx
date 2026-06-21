import { useProjectStore } from './store/useProjectStore';
import Step1_Script from './components/Step1_Script';
import Step2_Images from './components/Step2_Images';
import Step3_Voice from './components/Step3_Voice';
import Step4_Template from './components/Step4_Template';
import ResultView from './components/ResultView';

function App() {
  const { currentStep, blogUrl, setBlogUrl, statusMode, handleStartAnalysis } = useProjectStore();

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex font-sans antialiased">
      
      {/* 글로벌 상태 락 스피너 로딩 바 */}
      {statusMode === 'analyzing' && <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-black/80 text-center"><div className="w-12 h-12 rounded-full border-4 border-blue-500/10 border-t-blue-500 animate-spin mb-4"></div><p className="font-semibold text-slate-300">실시간 블로그 텍스트 파싱 및 GPT-4o 맞춤형 대본 컴파일 중...</p></div>}
      {statusMode === 'processing_tts' && <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-black/80 text-center"><div className="w-12 h-12 rounded-full border-4 border-emerald-500/10 border-t-emerald-500 animate-spin mb-4"></div><p className="font-semibold text-emerald-400">선택 성우 AI 보이스 엔진 가동 및 오디오 주파수 트랙 합성 중...</p></div>}
      {statusMode === 'rendering_video' && <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-black/80 text-center"><div className="w-12 h-12 rounded-full border-4 border-indigo-500/10 border-t-indigo-500 animate-spin mb-4"></div><p className="font-semibold text-indigo-400">FFmpeg 컴파일러 구동: 9:16 비디오 트랙 자막 인코딩 및 멀티플렉싱 처리 중...</p></div>}

      {/* 좌측 고정식 위저드 사이드바 */}
      <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col p-6 shrink-0">
        <div className="flex items-center gap-2 mb-8 px-2"><span className="w-3 h-3 rounded-full bg-blue-500 animate-pulse"></span><span className="font-black tracking-wider text-lg">SuperShorts AI</span></div>
        <nav className="flex flex-col gap-1 flex-1">
          {[
            { id: 1, name: '기획 및 대본' },
            { id: 2, name: '주요 이미지 선택' },
            { id: 3, name: '목소리 선택' },
            { id: 4, name: '템플릿 매칭' }
          ].map((st) => (
            <div key={st.id} className={`flex items-center gap-3 px-3 py-3 rounded-xl text-sm font-bold transition-all ${currentStep === st.id ? 'bg-blue-600 text-white shadow-lg' : currentStep > st.id ? 'text-blue-400 bg-blue-500/5' : 'text-slate-500'}`}>
              <span className={`w-5 h-5 rounded-full flex items-center justify-center text-xs border ${currentStep === st.id ? 'border-white bg-white text-blue-600' : currentStep > st.id ? 'border-blue-400 bg-blue-500/10' : 'border-slate-700'}`}>{st.id}</span>
              {st.name}
            </div>
          ))}
        </nav>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 border-b border-slate-900 flex items-center justify-between px-8 bg-slate-900/40 backdrop-blur-md">
          <span className="text-sm font-bold text-slate-400">대시보드 &gt; 프로젝트 가공</span>
          <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center font-bold text-sm">USER</div>
        </header>

        <main className="flex-1 p-8 overflow-y-auto max-w-6xl w-full mx-auto">
          {/* Step 0: 주소 입력 메인 스테이지 */}
          {currentStep === 0 && !statusMode && (
            <div className="flex flex-col items-center justify-center min-h-[70vh] text-center max-w-2xl mx-auto">
              <span className="text-sm font-bold text-blue-400 tracking-wider uppercase mb-2">네이버 블로그 링크 하나로 영상을 바로 만듭니다.</span>
              <h2 className="text-3xl font-black text-white mb-8">링크만 넣고 바로 시작</h2>
              <div className="w-full bg-slate-900 border border-slate-800 rounded-3xl p-8 shadow-2xl flex flex-col gap-5">
                <input type="url" className="w-full bg-slate-950 border border-slate-800 rounded-2xl p-5 text-base text-slate-200 placeholder-slate-700 focus:outline-none focus:border-blue-500" placeholder="https://blog.naver.com/아이디/포스팅번호" value={blogUrl} onChange={(e) => setBlogUrl(e.target.value)} />
                <button onClick={handleStartAnalysis} className="w-full bg-blue-600 hover:bg-blue-500 font-bold py-4 rounded-xl shadow-lg transition-all text-base">다음 단계 분석 실행 ➔</button>
              </div>
            </div>
          )}

          {/* Zustand 라우팅 매트릭스 지휘 */}
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