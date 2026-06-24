import { useProjectStore } from '../store/useProjectStore';

export default function ResultView() {
  const { projectData, setCurrentStep, resetProject } = useProjectStore();

  return (
    <div className="animate-fade-in">
      {/* 상단 네비게이션 */}
      <div className="flex items-center justify-between mb-6">
        <button onClick={() => setCurrentStep(4)} className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-800 font-bold transition-colors">← 스타일 다시 고르기</button>
        <button onClick={resetProject} className="text-sm font-bold text-indigo-600 hover:text-indigo-700">＋ 새 영상 만들기</button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-7">
        {/* 영상 플레이어 */}
        <div className="lg:col-span-5">
          <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm flex flex-col items-center">
            <span className="text-xs text-indigo-600 font-bold mb-3 self-start">완성된 영상</span>
            <video src={projectData.videoUrl} controls className="w-full aspect-[9/16] bg-black rounded-xl mb-4" />

            <a href={projectData.videoUrl} download="supershorts_video.mp4"
              className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3.5 rounded-xl text-center text-sm transition-all block mb-2.5">
              영상 다운로드
            </a>

            {/* ✅ 다운로드 후 뒤로/처음으로 버튼 */}
            <div className="flex gap-2.5 w-full">
              <button onClick={() => setCurrentStep(4)}
                className="w-1/2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold py-3 rounded-xl text-center text-sm transition-all">
                ← 뒤로
              </button>
              <button onClick={resetProject}
                className="w-1/2 bg-slate-900 hover:bg-slate-800 text-white font-bold py-3 rounded-xl text-center text-sm transition-all">
                새 영상 만들기
              </button>
            </div>
          </div>
        </div>

        {/* 우측 정보 */}
        <div className="lg:col-span-7 flex flex-col gap-5">
          <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
            <h4 className="text-base font-black text-slate-900 mb-3 pb-3 border-b border-gray-200">장면별 자막</h4>
            <div className="flex flex-col gap-2.5 max-h-[340px] overflow-y-auto pr-1">
              {projectData.scenes.map((scene) => (
                <div key={scene.id} className="bg-slate-50 border border-gray-200 rounded-xl p-3.5">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[11px] font-bold text-slate-500 bg-white px-2 py-0.5 rounded border border-gray-200">장면 {scene.id}</span>
                    <span className="text-[11px] text-indigo-600 font-bold">목소리 · {projectData.selectedVoice}</span>
                  </div>
                  <p className="text-sm text-slate-700 leading-relaxed">{scene.script}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
            <span className="text-xs font-bold text-slate-400">원본 글</span>
            <p className="text-sm text-slate-700 mt-1.5 leading-relaxed">
              <strong className="text-slate-900">'{projectData.title}'</strong> 글을 바탕으로 만든 영상이에요.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
