import { EmptyState } from "../EmptyState";
import { PanelFrame } from "../PanelFrame";

type Dependency = {
  from_sub_task_id: string;
  to_sub_task_id: string;
};

type Subtask = {
  id: string;
  name: string;
};

type Props = {
  dependencies: Dependency[];
  subtasks: Subtask[];
};

export function DependencyList({ dependencies, subtasks }: Props) {
  const subtaskMap = new Map(subtasks.map((item) => [item.id, item.name]));

  return (
    <PanelFrame title="依赖关系" description="用于判断当前链路是否存在阻塞节点或待满足的前置任务。">
      {dependencies.length === 0 ? (
        <EmptyState
          title="当前没有阻塞依赖"
          description="如果子任务之间形成前后置关系，这里会按来源与目标结构化展示。"
          aside="当前链路可直接推进"
        />
      ) : (
        <div className="dependency-list">
          {dependencies.map((dependency, index) => (
            <article key={`${dependency.from_sub_task_id}-${dependency.to_sub_task_id}-${index}`} className="dependency-link">
              <span className="dependency-node">{subtaskMap.get(dependency.from_sub_task_id) || dependency.from_sub_task_id}</span>
              <span className="dependency-link__arrow">→</span>
              <span className="dependency-node">{subtaskMap.get(dependency.to_sub_task_id) || dependency.to_sub_task_id}</span>
            </article>
          ))}
        </div>
      )}
    </PanelFrame>
  );
}
