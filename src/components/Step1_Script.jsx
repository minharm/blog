import { useProjectStore } from '../store/useProjectStore';

export default function Step1_Script() {
  const { projectData, handleScriptChange, setCurrentStep } = useProjectStore();

  return (
    <div className="animate-fade-in flex flex-col gap-5">
      <div className="flex justify-between items-center">
        <button onClick={() => setCurrentStep(0)} className="text-sm text-slate-500 hover:text-slate-300 font-bold">← 이전으로</button>
        <span className="text-xs font-bold text-blue-400 bg-blue-500/10 px-3 py-1 rounded-full border border-blue-500/20">Step 1</span>
      </div>
      <h3 className="text-2xl font-black text-white">생성된 숏츠 대본 편집</h3>
      <div className="flex flex-col gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex flex-col gap-2">
          <span className="text-xs font-black text-rose-400 uppercase">[Hook] 도입부 자막</span>
          <input type="text" value={projectData.script.hook} onChange={(e) => handleScriptChange('hook', e.target.value)} className="w-full bg-slate-950 border border-slate-800 rounded-xl p-4 text-sm text-slate-200 focus:outline-none focus:border-blue-500" />
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex flex-col gap-2">
          <span className="text-xs font-black text-emerald-400 uppercase">[Body] 몸통부 핵심 요약 자막</span>
          <textarea value={projectData.script.body} onChange={(e) => handleScriptChange('body', e.target.value)} className="w-full bg-slate-950 border border-slate-800 rounded-xl p-4 text-sm text-slate-200 focus:outline-none focus:border-blue-500 resize-none" rows={4} />
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex flex-col gap-2">
          <span className="text-xs font-black text-blue-400 uppercase">[Ending] 아웃트로 자막</span>
          <input type="text" value={projectData.script.ending} onChange={(e) => handleScriptChange('ending', e.target.value)} className="w-full bg-slate-950 border border-slate-800 rounded-xl p-4 text-sm text-slate-200 focus:outline-none focus:border-blue-500" />
        </div>
      </div>
      <button onClick={() => setCurrentStep(2)} className="px-8 py-3.5 bg-blue-600 hover:bg-blue-500 font-bold rounded-xl text-sm transition-all self-end mt-2 shadow-md">대본 확정 및 이미지 선택 ➔</button>
    </div>
  );
}