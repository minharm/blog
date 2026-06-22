import { useProjectStore } from '../store/useProjectStore';

const VOICES = [
  { id: 'none', name: '자막만 사용', desc: '목소리 없이 자막과 배경음악으로만', icon: '💬' },
  { id: 'alloy', name: '나라', desc: '맑고 또렷한 정보 전달 여성 톤', icon: '🙋\u200d♀️' },
  { id: 'nova', name: '봄달', desc: '자연스러운 일상 브이로그 여성 톤', icon: '🌸' },
  { id: 'shimmer', name: '유진', desc: '화사하고 텐션 높은 쇼핑 호스트 톤', icon: '✨' },
  { id: 'echo', name: '재민', desc: '신뢰감 있는 아나운서 남성 톤', icon: '🎙️' },
  { id: 'onyx', name: '민상', desc: '박진감 넘치는 스포츠 MC 남성 톤', icon: '🔥' },
  { id: 'fable', name: '동수', desc: '차분하게 팁을 읽어주는 리뷰 남성 톤', icon: '🎧' },
];

export default function Step3_Voice() {
  const { projectData, setSelectedVoice, playVoiceSample, handleVoiceGeneration, setCurrentStep } = useProjectStore();

  return (
    <div className="animate-fade-in">
      <button onClick={() => setCurrentStep(2)} className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-slate-800 font-bold mb-4 transition-colors">← 이전</button>
      <div className="flex items-center gap-2 mb-1">
        <span className="text-[11px] font-bold text-indigo-600 bg-indigo-50 px-2.5 py-1 rounded-full">STEP 3</span>
      </div>
      <h3 className="text-2xl font-black text-slate-900">목소리를 골라 주세요</h3>
      <p className="text-slate-500 text-sm mt-1.5 mb-6">영상에서 대본을 읽어줄 목소리예요. 샘플을 들어보고 선택하세요.</p>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5 mb-8">
        {VOICES.map((voice) => {
          const selected = projectData.selectedVoice === voice.id;
          return (
            <div key={voice.id} onClick={() => setSelectedVoice(voice.id)}
              className={`p-4 rounded-2xl border cursor-pointer transition-all ${selected ? 'bg-indigo-50 border-indigo-400 ring-2 ring-indigo-500/20' : 'bg-white border-gray-200 hover:border-gray-300'}`}>
              <div className="flex items-start gap-3 mb-3">
                <span className="text-xl shrink-0">{voice.icon}</span>
                <div className="min-w-0">
                  <span className="font-bold text-slate-900 text-sm block">{voice.name}</span>
                  <p className="text-xs text-slate-400 leading-relaxed mt-0.5">{voice.desc}</p>
                </div>
                {selected && <span className="ml-auto text-indigo-600 font-bold shrink-0">✓</span>}
              </div>
              {voice.id !== 'none' && (
                <button onClick={(e) => playVoiceSample(voice.id, e)}
                  className="w-full text-xs font-bold bg-slate-50 hover:bg-indigo-600 text-slate-600 hover:text-white py-2.5 rounded-xl transition-all border border-gray-200 hover:border-indigo-600">
                  ▶ 샘플 듣기
                </button>
              )}
            </div>
          );
        })}
      </div>

      <div className="flex justify-end">
        <button onClick={handleVoiceGeneration}
          className="px-7 py-3.5 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl text-sm transition-all">
          스타일 선택 →
        </button>
      </div>
    </div>
  );
}
