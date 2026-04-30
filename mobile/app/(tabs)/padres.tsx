import ChatModuleScreen from "../../src/components/ChatModuleScreen";

export default function PadresScreen() {
  return (
    <ChatModuleScreen
      module="modo_padres"
      title="Modo Padres"
      placeholder="Describe la situación que quieres trabajar..."
      companionName="Guía"
      companionSubtitle="Espacio práctico y calmado para orientación familiar."
      avatarVariant="guide"
      quickExamples={[
        "Mi hijo se frustra muy rápido",
        "¿Cómo puedo calmar una crisis?",
        "Necesito una rutina sencilla",
        "¿Cómo mejorar la comunicación en casa?",
      ]}
    />
  );
}