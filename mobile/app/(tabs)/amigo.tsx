import ChatModuleScreen from "../../src/components/ChatModuleScreen";

export default function AmigoScreen() {
  return (
    <ChatModuleScreen
      module="amigo_imaginario"
      title="Amigo Imaginario"
      placeholder="Escribe lo que sientes o lo que quieras contar..."
      companionName="Lumi"
      companionSubtitle="Conversa con calma, juega suavemente y siente compañía."
      avatarVariant="lumi"
      quickExamples={[
        "Hola Lumi",
        "Hoy me siento triste",
        "Cuéntame un cuento corto",
        "Quiero un juego tranquilo",
      ]}
    />
  );
}