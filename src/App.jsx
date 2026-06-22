import { useProjectStore } from './store/useProjectStore';
import Step1_Script from './components/Step1_Script';
import Step2_Images from './components/Step2_Images';
import Step3_Voice from './components/Step3_Voice';
import Step4_Template from './components/Step4_Template';
import ResultView from './components/ResultView';

function App() {
  const { currentStep, blogUrl, setBlogUrl, statusMode, handleStartAnalysis } = useProjectStore();

  return (
    // 🎯 테마 개선: bg-slate-950(기존 블랙)을 깊이감 있는 slate-900으로 올리고, 텍스트 가독성을 text-slate-100으로 상향
    <div className="min-h-screen bg-slate-900 text-slate-100 flex font-sans antialiased text-base">
      
      {/* 글로벌 로딩 상태 바 (컨트라스트 대폭 강화) */}
      {statusMode === 'analyzing' && (
        <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-black/85 text-center">
          <div className="w-16 h-16 rounded-full border-4 border-blue-500/20 border-t-blue-500 animate-spin mb-4"></div>
          <p className="font-bold text-xl text-white">실시간 블로그 텍스트 파싱 및 GPT-4o 맞춤형 대본 컴파일 중...</p>
        </div>
      )}
      {statusMode === 'processing_tts' && (
        <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-black/85 text-center">
          <div className="w-16 h-16 rounded-full border-4 border-emerald-500/20 border-t-emerald-500 animate-spin mb-4"></div>
          <p className="font-bold text-xl text-emerald-400">선택 성우 AI 보이스 가동 및 오디오 주파수 트랙 합성 중...</p>
        </div>
      )}
      {statusMode === 'rendering_video' && (
        <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-black/85 text-center">
          <div className="w-16 h-16 rounded-full border-4 border-indigo-500/20 border-t-indigo-500 animate-spin mb-4"></div>
          <p className="font-bold text-xl text-indigo-400">FFmpeg 컴파일러 구동: 9:16 비디오 트랙 자막 인코딩 및 멀티플렉싱 처리 중...</p>
        </div>
      )}

      {/* 🛠️ 좌측 고정 사이드바 (두께감 및 테마 선명도 보강) */}
      <aside className="w-72 bg-slate-950 border-r border-slate-800 flex flex-col p-6 shrink-0">
        {/* 🎯 [타이틀 변경]: 네이버 블로그 숏츠 AI 적용 및 크기 업스케일링 */}
        <div className="flex items-center gap-2.5 mb-10 px-2">
          <span className="w-3.5 h-3.5 rounded-full bg-blue-500 animate-pulse"></span>
          <span className="font-black tracking-tight text-xl text-white">네이버 블로그 숏츠 AI</span>
        </div>
        
        {/* 사이드바 네비게이션 가독성 업그레이드 (글자 크기 및 컨트라스트 대폭 증가) */}
        <nav className="flex flex-col gap-2 flex-1">
          {[
            { id: 1, name: '기획 및 대본 편집' },
            { id: 2, name: '주요 이미지 선택' },
            { id: 3, name: '성우 목소리 지정' },
            { id: 4, name: '스타일 템플릿 매칭' }
          ].map((st) => (
            <div 
              key={st.id} 
              className={`flex items-center gap-4 px-4 py-4 rounded-xl text-base font-black transition-all ${
                currentStep === st.id 
                  ? 'bg-blue-600 text-white shadow-xl shadow-blue-600/20' 
                  : currentStep > st.id 
                    ? 'text-blue-400 bg-blue-500/10 border border-blue-500/20' 
                    : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold border ${
                currentStep === st.id 
                  ? 'border-white bg-white text-blue-600' 
                  : currentStep > st.id 
                    ? 'border-blue-400 bg-blue-500/20 text-blue-400' 
                    : 'border-slate-600 text-slate-400'
              }`}>
                {st.id}
              </span>
              {st.name}
            </div>
          ))}
        </nav>
      </aside>

      {/* 우측 메인 대시보드 코어 영역 */}
      <div className="flex-1 flex flex-col min-w-0 bg-slate-900">
        <header className="h-16 border-b border-slate-800 flex items-center justify-between px-8 bg-slate-950/40 backdrop-blur-md">
          <span className="text-sm font-bold text-slate-300">대시보드 &gt; 프로젝트 자동 생성 공정</span>
          <div className="w-9 h-9 rounded-full bg-blue-600 flex items-center justify-center font-black text-xs text-white shadow-md">USER</div>
        </header>

        <main className="flex-1 p-8 overflow-y-auto max-w-6xl w-full mx-auto">
          {/* Step 0: 주소 입력 메인 스테이지 (시인성 200% 파워 업) */}
          {currentStep === 0 && !statusMode && (
            <div className="flex flex-col items-center justify-center min-h-[65vh] text-center max-w-3xl mx-auto animate-fade-in">
              <span className="text-sm font-extrabold text-blue-400 tracking-wider bg-blue-500/10 px-4 py-1.5 rounded-full border border-blue-500/20 uppercase mb-4">
                네이버 블로그 링크 하나로 숏폼 영상 제작 파이프라인 가동
              </span>
              <h2 className="text-4xl font-black text-white tracking-tight mb-8">블로그 주소를 입력하고 시작하세요</h2>
              
              <div className="w-full bg-slate-950 border border-slate-800 rounded-3xl p-8 shadow-2xl flex flex-col gap-6">
                {/* 🎯 개선: placeholder-slate-700(안 보임)을 placeholder-slate-400으로 교체하여 시인성 확보 */}
                <input 
                  type="url" 
                  className="w-full bg-slate-900 border border-slate-700 rounded-2xl p-5 text-lg text-white font-medium placeholder-slate-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all shadow-inner" 
                  placeholder="https://blog.naver.com/아이디/포스트번호 양식으로 입력하세요" 
                  value={blogUrl} 
                  onChange={(e) => setBlogUrl(e.target.value)} 
                />
                <button 
                  onClick={handleStartAnalysis} 
                  className="w-full bg-blue-600 hover:bg-blue-500 text-white font-black py-4.5 rounded-2xl shadow-xl shadow-blue-600/10 transition-all text-lg tracking-wide cursor-pointer"
                >
                  블로그 본문 분석 및 대본 생성하기 ➔
                </button>
              </div>
            </div>
          )}

          {/* Zustand 라우팅 매트릭스 매핑 컴포넌트 */}
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