import { useProjectStore } from '../store/useProjectStore';

// value = 실제 OpenAI 보이스명 / gpt-4o-mini-tts 톤 지시로 밝게 읽힘
const VOICES = [
  { id: 'none', name: '자막만 사용', desc: '목소리 없이 자막·배경음악만', icon: '💬' },
  { id: 'coral', name: '밝은 진행자', desc: '쇼츠에 잘 어울리는 밝고 친근한 톤', icon: '✨', hot: true },
  { id: 'nova', name: '발랄한 여성', desc: '경쾌하고 에너지 있는 여성 톤', icon: '🌸', hot: true },
  { id: 'shimmer', name: '화사한 여성', desc: '화사하고 텐션 높은 쇼핑 호스트 톤', icon: '💫', hot: true },
  { id: 'sage', name: '편안한 내레이션', desc: '부드럽고 차분한 설명 톤', icon: '🍃' },
  { id: 'alloy', name: '깔끔한 기본', desc: '중립적이고 또렷한 기본 톤', icon: '🙂' },
  { id: 'echo', name: '또렷한 남성', desc: '신뢰감 있는 남성 내레이션', icon: '🎙️' },
  { id: 'onyx', name: '저음 남성', desc: '차분하고 묵직한 남성 톤', icon: '🎧' },
];

export default function Step3_Voice() {
  const { projectData, setSelectedVoice, playVoiceSample, handleVoiceGeneration, setCurrentStep } = useProjectStore();

  return (
    <div className="animate-fade-in">
      <button onClick={() => setCurrentStep(2)} className="inline-flex items-center gap-1 text-base text-slate-500 hover:text-slate-800 font-bold mb-4 transition-colors">← 이전</button>
      <div className="flex items-center gap-2 mb-1">
        <span className="text-xs font-bold text-indigo-600 bg-indigo-50 px-2.5 py-1 rounded-full">STEP 3</span>
      </div>
      <h3 className="text-2xl font-black text-slate-900">목소리를 골라 주세요</h3>
      <p className="text-slate-500 text-base mt-1.5 mb-6">유튜브 쇼츠에 어울리는 밝은 목소리들이에요. 샘플을 들어보고 선택하세요.</p>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5 mb-8">
        {VOICES.map((voice) => {
          const selected = projectData.selectedVoice === voice.id;
          return (
            <div key={voice.id} onClick={() => setSelectedVoice(voice.id)}
              className={`p-4 rounded-2xl border cursor-pointer transition-all ${selected ? 'bg-indigo-50 border-indigo-400 ring-2 ring-indigo-500/20' : 'bg-white border-gray-200 hover:border-gray-300'}`}>
              <div className="flex items-start gap-3 mb-3">
                <span className="text-2xl shrink-0">{voice.icon}</span>
                <div className="min-w-0">
                  <span className="font-bold text-slate-900 text-base flex items-center gap-1.5">
                    {voice.name}
                    {voice.hot && <span className="text-[10px] font-bold text-rose-500 bg-rose-50 px-1.5 py-0.5 rounded">인기</span>}
                  </span>
                  <p className="text-sm text-slate-400 leading-relaxed mt-0.5">{voice.desc}</p>
                </div>
                {selected && <span className="ml-auto text-indigo-600 font-bold shrink-0">✓</span>}
              </div>
              {voice.id !== 'none' && (
                <button onClick={(e) => playVoiceSample(voice.id, e)}
                  className="w-full text-sm font-bold bg-slate-50 hover:bg-indigo-600 text-slate-600 hover:text-white py-2.5 rounded-xl transition-all border border-gray-200 hover:border-indigo-600">
                  ▶ 샘플 듣기
                </button>
              )}
            </div>
          );
        })}
      </div>

      <div className="flex justify-end">
        <button onClick={handleVoiceGeneration}
          className="px-7 py-3.5 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl text-base transition-all">
          스타일 선택 →
        </button>
      </div>
    </div>
  );
}
