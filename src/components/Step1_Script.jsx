import { useProjectStore } from '../store/useProjectStore';

// 백엔드와 동일 기준(글자수 * 0.18초)으로 예상 노출 시간 계산
const estSec = (t) => Math.max(0, Math.round((t?.length || 0) * 0.18 * 10) / 10);

const FIELDS = [
  { key: 'hook', label: '도입', hint: '첫 1초에 시선을 잡는 한 문장', accent: 'text-rose-500', bg: 'bg-rose-50', multiline: false, max: 40 },
  { key: 'body', label: '핵심', hint: '본문에서 가장 중요한 정보 요약', accent: 'text-emerald-600', bg: 'bg-emerald-50', multiline: true, max: 120 },
  { key: 'ending', label: '마무리', hint: '구독·저장을 유도하는 마무리 문구', accent: 'text-indigo-600', bg: 'bg-indigo-50', multiline: false, max: 40 },
];

function StepHeader({ onBack, step, title, sub }) {
  return (
    <div className="mb-6">
      <button onClick={onBack} className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-800 font-bold mb-4 transition-colors">
        ← 이전
      </button>
      <div className="flex items-center gap-2 mb-1">
        <span className="text-[11px] font-bold text-indigo-600 bg-indigo-50 px-2.5 py-1 rounded-full">STEP {step}</span>
      </div>
      <h3 className="text-2xl font-black text-slate-900">{title}</h3>
      {sub && <p className="text-slate-500 text-sm mt-1.5">{sub}</p>}
    </div>
  );
}

export default function Step1_Script() {
  const { projectData, handleScriptChange, setCurrentStep } = useProjectStore();
  const total = ['hook', 'body', 'ending'].reduce((a, k) => a + estSec(projectData.script[k]), 0);

  return (
    <div className="animate-fade-in max-w-3xl">
      <StepHeader onBack={() => setCurrentStep(0)} step={1} title="대본을 다듬어 주세요"
        sub="AI가 만든 초안이에요. 도입·핵심·마무리 세 문장을 자유롭게 고칠 수 있어요." />

      {projectData.title && (
        <div className="mb-5 rounded-xl bg-white border border-gray-200 px-4 py-3 text-sm">
          <span className="text-slate-400 font-bold mr-2">원본 글</span>
          <span className="text-slate-700 font-medium">{projectData.title}</span>
        </div>
      )}

      <div className="flex flex-col gap-4">
        {FIELDS.map((f) => {
          const val = projectData.script[f.key] || '';
          const over = val.length > f.max;
          return (
            <div key={f.key} className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className={`text-xs font-black px-2 py-0.5 rounded ${f.bg} ${f.accent}`}>{f.label}</span>
                  <span className="text-xs text-slate-400">{f.hint}</span>
                </div>
                <span className={`text-[11px] font-mono ${over ? 'text-rose-500 font-bold' : 'text-slate-400'}`}>
                  {val.length}자 · 약 {estSec(val)}초
                </span>
              </div>
              {f.multiline ? (
                <textarea value={val} rows={3}
                  onChange={(e) => handleScriptChange(f.key, e.target.value)}
                  className="w-full bg-slate-50 border border-gray-200 rounded-xl p-3.5 text-[15px] text-slate-800 leading-relaxed focus:outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-500/20 resize-none transition-all" />
              ) : (
                <input type="text" value={val}
                  onChange={(e) => handleScriptChange(f.key, e.target.value)}
                  className="w-full bg-slate-50 border border-gray-200 rounded-xl p-3.5 text-[15px] text-slate-800 focus:outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-500/20 transition-all" />
              )}
              {over && <p className="text-[11px] text-rose-500 mt-2 font-medium">권장 {f.max}자보다 길어요. 짧을수록 자막이 잘 읽혀요.</p>}
            </div>
          );
        })}
      </div>

      <div className="flex items-center justify-between mt-6">
        <span className="text-sm text-slate-400">예상 영상 길이 <strong className="text-slate-700">약 {Math.round(total)}초</strong></span>
        <button onClick={() => setCurrentStep(2)}
          className="px-7 py-3.5 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl text-sm transition-all">
          이미지 선택 →
        </button>
      </div>
    </div>
  );
}
