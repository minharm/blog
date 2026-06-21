import { useProjectStore } from '../store/useProjectStore';

export default function ResultView() {
  const { projectData } = useProjectStore();

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 animate-fade-in">
      <div className="lg:col-span-5 flex flex-col gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 flex flex-col items-center shadow-xl w-full">
          <span className="text-xs text-blue-400 font-bold mb-3 self-start uppercase">출력 비디오 플레이어</span>
          <video src={projectData.videoUrl} controls className="w-full aspect-[9/16] bg-black rounded-2xl border border-slate-800 mb-5 shadow-2xl" />
          <a href={projectData.videoUrl} download="SuperShorts_AI_Video.mp4" className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3.5 rounded-xl text-center text-sm shadow-lg shadow-blue-600/10 transition-all block">📥 숏츠 영상 다운로드</a>
        </div>
      </div>
      <div className="lg:col-span-7 flex flex-col gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl">
          <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
            <h4 className="text-base font-black text-white">📋 상세 장면 콘티 타임라인</h4>
          </div>
          <div className="flex flex-col gap-3 max-h-[340px] overflow-y-auto pr-1">
            {projectData.scenes.map((scene) => (
              <div key={scene.id} className="bg-slate-950 border border-slate-800/60 rounded-xl p-4 flex flex-col gap-2">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="bg-slate-900 text-slate-300 px-2 py-0.5 rounded border border-slate-800">Scene 0{scene.id} ({scene.time || '가변타임'})</span>
                  <span className="text-blue-400 font-bold">🎙️ Voice: {projectData.selectedVoice}</span>
                </div>
                <div className="bg-slate-900/40 p-3 rounded-lg border border-slate-800/40 text-xs">
                  <span className="text-[10px] text-rose-400 font-bold block mb-1">[매핑 자막]</span>
                  <p className="text-slate-200 font-medium leading-relaxed">{scene.script}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl flex flex-col gap-3">
          <span className="text-xs font-bold text-slate-400">쇼츠 플랫폼 팩 고도화 요약</span>
          <div className="bg-slate-950 border border-slate-800 p-4 rounded-xl text-xs text-slate-400 leading-relaxed">
            본 영상은 블로그 타이틀 <strong className="text-slate-200">'{projectData.title}'</strong>의 소스를 GPT-4o 브레인을 거쳐 빌드한 프리미엄 비디오 에셋입니다.
          </div>
        </div>
      </div>
    </div>
  );
}