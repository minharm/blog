import { useProjectStore } from '../store/useProjectStore';

export default function Step3_Voice() {
  const { projectData, setSelectedVoice, playVoiceSample, handleVoiceGeneration, setCurrentStep } = useProjectStore();

  const voicePool = [
    { id: 'none', name: '🔇 자막 전용 모드', desc: '목소리 송출 없이 트렌디한 자막 효과로만 가동' },
    { id: 'alloy', name: '나라 (20대 여성)', desc: '맑고 똑 부러지는 정보 유튜버 쇼츠 전용' },
    { id: 'echo', name: '재민 (ASMR 남성)', desc: '중후하고 신뢰감 높은 목소리 기획 톤' },
    { id: 'onyx', name: '민상 (스포츠 MC)', desc: '바이럴, 챌린지 전용 하이 텐션 웅변 성우' },
    { id: 'nova', name: '봄달 (브이로그 여)', desc: '감성적이고 자연스러운 일상 공유 톤' },
    { id: 'shimmer', name: '민우 (게임 캐스터)', desc: '활기차고 오락성 강한 엔터테인먼트 사운드' },
    { id: 'fable', name: '보이스 아나운서', desc: '뉴스룸 사양의 정갈하고 차분한 브로드캐스팅' },
    { id: '유진', name: '쇼핑 호스트', desc: '제품 리뷰 및 쿠팡 파트너스 셀링 특화 마케터' }
  ];

  return (
    <div className="animate-fade-in">
      <div className="flex justify-between items-center mb-4">
        <button onClick={() => setCurrentStep(2)} className="text-sm text-slate-500 hover:text-slate-300 font-bold">← 이전으로</button>
        <span className="text-xs font-bold text-blue-400 uppercase">Step 3</span>
      </div>
      <h3 className="text-2xl font-black text-white mb-6">성우 목소리를 선택해주세요</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {voicePool.map((voice) => (
          <div key={voice.id} onClick={() => setSelectedVoice(voice.id)} className={`p-5 rounded-2xl border cursor-pointer flex flex-col justify-between transition-all ${projectData.selectedVoice === voice.id ? 'bg-blue-600/10 border-blue-500 shadow-lg' : 'bg-slate-900 border-slate-800 hover:border-slate-700'}`}>
            <div>
              <span className="font-bold text-white text-sm block mb-1">{voice.name}</span>
              <p className="text-[11px] text-slate-400 leading-relaxed mb-4">{voice.desc}</p>
            </div>
            {voice.id !== 'none' && (
              <button onClick={(e) => playVoiceSample(voice.id, e)} className="w-full text-[11px] font-bold bg-slate-950 hover:bg-blue-600 text-slate-300 hover:text-white py-2.5 rounded-xl transition-all border border-slate-800">🔊 실제 목소리 샘플 듣기</button>
            )}
          </div>
        ))}
      </div>
      <button onClick={handleVoiceGeneration} className="px-8 py-3.5 bg-blue-600 hover:bg-blue-500 font-bold rounded-xl text-sm transition-all shadow-md float-right">음성 채널 확정 및 다음 단계 ➔</button>
    </div>
  );
}