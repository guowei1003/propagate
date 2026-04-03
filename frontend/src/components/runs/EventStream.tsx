import { buildTimelineEvent, type RunEventPayload } from "../../lib/events";
import { PanelFrame } from "../PanelFrame";
import { RawJsonBlock } from "../RawJsonBlock";
import { TimelineFeed } from "../TimelineFeed";

type Props = {
  events: RunEventPayload[];
  highlightId?: string;
};

export function EventStream({ events, highlightId }: Props) {
  return (
    <PanelFrame
      title="事件流"
      description="关注最新推进、失败线索和人工介入提示。"
      className="event-stream-panel"
    >
      <div className="stack">
        <TimelineFeed
          items={events.map((event, index) => buildTimelineEvent(event, index))}
          highlightId={highlightId}
          emptyTitle="事件流将在执行开始后出现"
          emptyDescription="订阅运行后，这里会持续显示最新执行事件。"
        />
        <RawJsonBlock title="查看原始事件数据" data={events} />
      </div>
    </PanelFrame>
  );
}
